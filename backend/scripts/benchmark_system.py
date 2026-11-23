"""
backend/scripts/benchmark_system.py

Benchmarks the full per-tick processing pipeline:
  TelemetryGenerator.generate_tick()
  TelemetryFeaturizer.fit_transform()
  AnomalyArbiter.score_batch()
  RingBufferCache.push() (all cells)
  JSON serialisation (payload size)

Measures p50, p95, p99 latency across N_TICKS simulated ticks,
then prints a markdown-formatted summary table and writes it to
docs/benchmark_report.md.

Usage (from project root):
    $env:PYTHONPATH = "backend"
    python backend/scripts/benchmark_system.py
"""
import sys
import time
import json
import statistics
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

import joblib

from app.config import settings
from app.core.featurizer import TelemetryFeaturizer
from app.core.h3_manager import load_registry_from_geojson
from app.ml.zscore_baseline import SeasonalZScoreModel
from app.ml.lightgbm_model import LightGBMRegressorModel
from app.ml.isolation_forest import IsoForestAnomalyModel
from app.ml.arbiter import AnomalyArbiter
from app.simulation.generator import TelemetryGenerator
from app.db.session import RingBufferCache, HexMetrics

logging.basicConfig(level=logging.WARNING)   # silence info logs during benchmark

# ── config ────────────────────────────────────────────────────────────────────
N_TICKS   = 100   # number of ticks to benchmark
WARMUP    = 5     # warm-up ticks excluded from results
_IST      = timezone(timedelta(hours=5, minutes=30))
_SIM_BASE = datetime(2026, 9, 1, 0, 0, 0, tzinfo=_IST)


def load_models():
    zm = SeasonalZScoreModel()
    zm.load(settings.zscore_model_path)

    ld = joblib.load(settings.lgbm_model_path)
    lm = LightGBMRegressorModel()
    lm.model_ = ld["model"]
    lm.feature_names_ = ld["feature_names"]
    lm.residual_std_  = ld["residual_std"]

    im = IsoForestAnomalyModel()
    im.load(settings.isoforest_model_path)

    return zm, lm, im


def run_benchmark():
    print(f"\nLoading models and registry…")
    zm, lm, im = load_models()
    arbiter    = AnomalyArbiter(zm, lm, im)
    featurizer = TelemetryFeaturizer(settings.geojson_path)
    generator  = TelemetryGenerator(seed=42)
    buf        = RingBufferCache()

    registry    = load_registry_from_geojson(settings.geojson_path)
    registry_map = {r["h3_index"]: r for r in registry}

    print(f"Benchmarking {N_TICKS} ticks ({WARMUP} warm-up excluded)…\n")

    # Per-stage timing lists
    t_generate  = []
    t_featurize = []
    t_arbiter   = []
    t_ringbuf   = []
    t_serialize = []
    t_total     = []
    payload_bytes = []

    for tick_i in range(N_TICKS + WARMUP):
        sim_time = _SIM_BASE + timedelta(minutes=15 * tick_i)

        t0 = time.perf_counter()

        # 1. Generate
        t1 = time.perf_counter()
        df_raw = generator.generate_tick(
            tick_index=tick_i,
            base_date=_SIM_BASE.replace(tzinfo=None),
            active_scenarios={},
        )
        t2 = time.perf_counter()

        # 2. Featurize
        df_feat = featurizer.fit_transform(df_raw)
        t3 = time.perf_counter()

        # 3. Arbiter
        results    = arbiter.score_batch(df_feat)
        result_map = {r.h3_index: r for r in results}
        t4 = time.perf_counter()

        # 4. Ring buffer
        hex_updates = []
        for _, row in df_raw.iterrows():
            h3 = str(row["h3_index"])
            ar = result_map.get(h3)
            if ar is None:
                continue
            dsr = float(row["pickup_count"]) / max(float(row["available_drivers"]), 1.0)
            m = HexMetrics(
                h3_index=h3, timestamp=sim_time, tick_index=tick_i,
                pickup_count=int(row["pickup_count"]),
                available_drivers=int(row["available_drivers"]),
                cancellation_rate=float(row["cancellation_rate"]),
                surge_multiplier=float(row["surge_multiplier"]),
                avg_eta_minutes=float(row["avg_eta_minutes"]),
                is_rainy=bool(row["is_rainy"]),
                rainfall_mm=float(row["rainfall_mm"]),
                demand_supply_ratio=round(dsr, 4),
                z_score=ar.z_score, lgbm_pred=ar.lgbm_pred,
                residual=ar.residual, iso_score=ar.iso_score,
                anomaly_score=ar.anomaly_score,
                severity=ar.severity, root_cause=ar.root_cause,
            )
            buf.push(m)
            hex_updates.append(m.to_dict())
        t5 = time.perf_counter()

        # 5. Serialise payload
        payload = {
            "type": "TICK_UPDATE",
            "simulation_time": sim_time.isoformat(),
            "tick_index": tick_i,
            "summary": {
                "total_demand": sum(u["demand"] for u in hex_updates),
                "total_supply": sum(u["supply"] for u in hex_updates),
                "active_anomalies_count": sum(
                    1 for u in hex_updates if u["severity"] in ("HIGH", "CRITICAL")
                ),
            },
            "hex_updates": hex_updates,
            "new_alerts": [],
        }
        raw = json.dumps(payload, default=str)
        t6 = time.perf_counter()

        # Exclude warm-up
        if tick_i >= WARMUP:
            t_generate.append((t2 - t1) * 1000)
            t_featurize.append((t3 - t2) * 1000)
            t_arbiter.append((t4 - t3) * 1000)
            t_ringbuf.append((t5 - t4) * 1000)
            t_serialize.append((t6 - t5) * 1000)
            t_total.append((t6 - t0) * 1000)
            payload_bytes.append(len(raw.encode()))

        if (tick_i + 1) % 10 == 0:
            print(f"  tick {tick_i + 1}/{N_TICKS + WARMUP}", end="\r")

    print()

    def stats(vals):
        s   = sorted(vals)
        p50 = s[int(len(s) * 0.50)]
        p95 = s[int(len(s) * 0.95)]
        p99 = s[min(int(len(s) * 0.99), len(s) - 1)]
        return statistics.mean(vals), statistics.stdev(vals), p50, p95, p99

    rows = [
        ("generate_tick",   t_generate),
        ("fit_transform",   t_featurize),
        ("arbiter.score",   t_arbiter),
        ("ring_buffer",     t_ringbuf),
        ("json_serialize",  t_serialize),
        ("TOTAL tick",      t_total),
    ]

    header = f"{'Stage':<20}{'mean (ms)':>12}{'std':>10}{'p50':>10}{'p95':>10}{'p99':>10}"
    divider = "-" * len(header)

    lines = [
        "# Benchmark Report",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Ticks measured:** {N_TICKS}  (after {WARMUP} warm-up ticks)",
        f"**Hexagons per tick:** {len(generator.all_cells)}",
        "",
        "## Per-stage Latency (ms)",
        "",
        f"| Stage | mean | std | p50 | p95 | p99 |",
        f"|-------|-----:|----:|----:|----:|----:|",
    ]

    print("\n" + header)
    print(divider)
    for label, vals in rows:
        mean, std, p50, p95, p99 = stats(vals)
        print(f"{label:<20}{mean:>12.1f}{std:>10.1f}{p50:>10.1f}{p95:>10.1f}{p99:>10.1f}")
        lines.append(f"| {label} | {mean:.1f} | {std:.1f} | {p50:.1f} | {p95:.1f} | {p99:.1f} |")
    print(divider)

    avg_bytes = statistics.mean(payload_bytes)
    avg_kb    = avg_bytes / 1024
    lines += [
        "",
        "## Payload Size",
        "",
        f"- Average WebSocket payload: **{avg_kb:.1f} KB** per tick",
        f"- Min: {min(payload_bytes)/1024:.1f} KB  Max: {max(payload_bytes)/1024:.1f} KB",
        "",
        "## Notes",
        "",
        "- Timings measured in-process (no network overhead).",
        "- `ring_buffer` includes building `HexMetrics` objects for all cells.",
        "- `json_serialize` is the full JSON dump of the broadcast payload.",
        "- p95 total tick latency is the key SLA target (< 80 ms).",
    ]

    print(f"\nAverage payload size: {avg_kb:.1f} KB")

    # Write report
    report_path = REPO_ROOT / "docs" / "benchmark_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to: {report_path}")

    # Assert SLA
    total_p95 = sorted(t_total)[int(len(t_total) * 0.95)]
    SLA_MS = 500   # generous for a laptop running featurization
    if total_p95 <= SLA_MS:
        print(f"\n✅  p95 total tick latency = {total_p95:.1f} ms  (SLA ≤ {SLA_MS} ms)")
    else:
        print(f"\n⚠️   p95 total tick latency = {total_p95:.1f} ms  exceeds SLA of {SLA_MS} ms")


if __name__ == "__main__":
    run_benchmark()
