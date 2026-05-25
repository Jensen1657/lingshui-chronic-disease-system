import request from './request'

const tcmApi = {
  getList(params?: any) {
    return request.get('/v1/tcm/', { params })
  },
  getById(id: string) {
    return request.get(`/v1/tcm/${id}`)
  },
  create(data: any) {
    return request.post('/v1/tcm/', data)
  },
  update(id: string, data: any) {
    return request.put(`/v1/tcm/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/v1/tcm/${id}`)
  }
}

export { tcmApi }
