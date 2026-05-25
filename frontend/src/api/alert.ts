import request from './request'

const alertApi = {
  getList(params?: any) {
    return request.get('/v1/alerts/', { params })
  },
  getById(id: string) {
    return request.get(`/v1/alerts/${id}`)
  },
  create(data: any) {
    return request.post('/v1/alerts/', data)
  },
  update(id: string, data: any) {
    return request.put(`/v1/alerts/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/v1/alerts/${id}`)
  }
}

export { alertApi }
