import { describe, it, expect } from 'vitest'
import {
  getSeverityColor,
  getSeverityHex,
  getSeverityClass,
} from '../lib/colorRamp'

describe('getSeverityColor', () => {
  it('returns green RGBA for NORMAL', () => {
    expect(getSeverityColor('NORMAL')).toEqual([12, 165, 85, 160])
  })
  it('returns blue RGBA for MEDIUM', () => {
    expect(getSeverityColor('MEDIUM')).toEqual([39, 110, 241, 180])
  })
  it('returns orange RGBA for HIGH', () => {
    expect(getSeverityColor('HIGH')).toEqual([252, 153, 60, 210])
  })
  it('returns red RGBA for CRITICAL', () => {
    expect(getSeverityColor('CRITICAL')).toEqual([244, 59, 0, 240])
  })
})

describe('getSeverityHex', () => {
  it('returns correct hex string for NORMAL', () => {
    expect(getSeverityHex('NORMAL')).toBe('#0ca555')
  })
  it('returns correct hex string for CRITICAL', () => {
    expect(getSeverityHex('CRITICAL')).toBe('#f43b00')
  })
})

describe('getSeverityClass', () => {
  it('contains bg-uber-red for CRITICAL', () => {
    expect(getSeverityClass('CRITICAL')).toContain('bg-uber-red')
  })
  it('contains bg-uber-green for NORMAL', () => {
    expect(getSeverityClass('NORMAL')).toContain('bg-uber-green')
  })
  it('contains bg-uber-orange for HIGH', () => {
    expect(getSeverityClass('HIGH')).toContain('bg-uber-orange')
  })
  it('contains bg-uber-blue for MEDIUM', () => {
    expect(getSeverityClass('MEDIUM')).toContain('bg-uber-blue')
  })
})
