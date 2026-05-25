import request from './request'

const assessmentApi = {
  getList(params?: any) {
    return request.get('/v1/assessments/', { params })
  },
  getById(id: string) {
    return request.get(`/v1/assessments/${id}`)
  },
  create(data: any) {
    return request.post('/v1/assessments/', data)
  },
  update(id: string, data: any) {
    return request.put(`/v1/assessments/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/v1/assessments/${id}`)
  }
}

export { assessmentApi }
