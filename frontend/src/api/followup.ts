import request from './request'

const followupApi = {
  getList(params?: any) {
    return request.get('/v1/followups/', { params })
  },
  getById(id: string) {
    return request.get(`/v1/followups/${id}`)
  },
  create(data: any) {
    return request.post('/v1/followups/', data)
  },
  update(id: string, data: any) {
    return request.put(`/v1/followups/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/v1/followups/${id}`)
  }
}

export { followupApi }
