import request from './request'

const selfReportApi = {
  getList(params?: any) {
    return request.get('/v1/self-reports/', { params })
  },
  getById(id: string) {
    return request.get(`/v1/self-reports/${id}`)
  },
  create(data: any) {
    return request.post('/v1/self-reports/', data)
  },
  update(id: string, data: any) {
    return request.put(`/v1/self-reports/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/v1/self-reports/${id}`)
  }
}

export { selfReportApi }
