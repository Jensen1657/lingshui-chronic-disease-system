import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePatientStore } from '../patient'

describe('Patient Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with empty patients list', () => {
    const store = usePatientStore()
    expect(store.patients).toEqual([])
    expect(store.total).toBe(0)
  })

  it('has loading state', () => {
    const store = usePatientStore()
    expect(store.loading).toBe(false)
  })

  it('has error state', () => {
    const store = usePatientStore()
    expect(store.error).toBeFalsy()
  })
})
