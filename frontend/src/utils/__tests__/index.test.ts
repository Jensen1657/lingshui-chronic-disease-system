import { describe, it, expect } from 'vitest'
import { formatDiseaseList, getRiskLevelColor, calculateAge } from '../index'

describe('formatDiseaseList', () => {
  it('formats disease codes to Chinese names', () => {
    expect(formatDiseaseList(['HYPERTENSION'])).toBe('高血压')
    expect(formatDiseaseList(['DIABETES'])).toBe('糖尿病')
    expect(formatDiseaseList(['HYPERTENSION', 'DIABETES'])).toBe('高血压, 糖尿病')
  })

  it('returns empty string for empty array', () => {
    expect(formatDiseaseList([])).toBe('')
  })

  it('returns original code for unknown disease', () => {
    expect(formatDiseaseList(['UNKNOWN'])).toBe('UNKNOWN')
  })
})

describe('getRiskLevelColor', () => {
  it('returns correct colors for risk levels', () => {
    expect(getRiskLevelColor('LOW')).toBe('success')
    expect(getRiskLevelColor('MEDIUM')).toBe('warning')
    expect(getRiskLevelColor('HIGH')).toBe('danger')
    expect(getRiskLevelColor('VERY_HIGH')).toBe('danger')
  })
})

describe('calculateAge', () => {
  it('calculates age from birth date', () => {
    const birthDate = '1990-01-01'
    const age = calculateAge(birthDate)
    expect(age).toBeGreaterThan(30)
    expect(age).toBeLessThan(40)
  })
})
