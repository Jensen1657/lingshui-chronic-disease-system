import request from './request'

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

const patientApi = {
  getList(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/v1/patients/', { params })
  },
  getById(id: string) {
    return request.get(`/v1/patients/${id}`)
  },
  create(data: any) {
    return request.post('/v1/patients/', data)
  },
  update(id: string, data: any) {
    return request.put(`/v1/patients/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/v1/patients/${id}`)
  }
}

export { patientApi }
