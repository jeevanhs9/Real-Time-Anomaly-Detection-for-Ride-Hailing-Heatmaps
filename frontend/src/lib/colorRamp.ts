import type { Severity } from '../types/telemetry'

// RGBA arrays consumed directly by Deck.gl layers
export const SEVERITY_COLORS: Record<Severity, [number, number, number, number]> = {
  NORMAL:   [12,  165,  85,  160],  // #0ca555  opacity 0.63
  MEDIUM:   [39,  110, 241,  180],  // #276ef1  opacity 0.71
  HIGH:     [252, 153,  60,  210],  // #fc993c  opacity 0.82
  CRITICAL: [244,  59,   0,  240],  // #f43b00  opacity 0.94
}

export function getSeverityColor(
  severity: Severity,
): [number, number, number, number] {
  return SEVERITY_COLORS[severity] ?? SEVERITY_COLORS.NORMAL
}

export const SEVERITY_HEX: Record<Severity, string> = {
  NORMAL:   '#0ca555',
  MEDIUM:   '#276ef1',
  HIGH:     '#fc993c',
  CRITICAL: '#f43b00',
}

export function getSeverityHex(severity: Severity): string {
  return SEVERITY_HEX[severity] ?? SEVERITY_HEX.NORMAL
}

/** Tailwind className pair for severity pills */
export function getSeverityClass(severity: Severity): string {
  switch (severity) {
    case 'CRITICAL': return 'bg-uber-red    text-white'
    case 'HIGH':     return 'bg-uber-orange text-uber-black'
    case 'MEDIUM':   return 'bg-uber-blue   text-white'
    default:         return 'bg-uber-green  text-white'
  }
}
