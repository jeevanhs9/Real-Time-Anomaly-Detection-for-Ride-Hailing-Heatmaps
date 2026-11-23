import type { Severity } from '../types/telemetry'

// RGBA arrays consumed directly by Deck.gl layers
export const SEVERITY_COLORS: Record<Severity, [number, number, number, number]> = {
  NORMAL:   [12,  165,  85,   62],  // #0ca555  opacity 0.24
  MEDIUM:   [39,  110, 241,  145],  // #276ef1  opacity 0.57
  HIGH:     [252, 153,  60,  185],  // #fc993c  opacity 0.73
  CRITICAL: [244,  59,   0,  225],  // #f43b00  opacity 0.88
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
