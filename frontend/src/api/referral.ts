import request from './request'

const referralApi = {
  getList(params?: any) {
    return request.get('/v1/referrals/', { params })
  },
  getById(id: string) {
    return request.get(`/v1/referrals/${id}`)
  },
  create(data: any) {
    return request.post('/v1/referrals/', data)
  },
  update(id: string, data: any) {
    return request.put(`/v1/referrals/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/v1/referrals/${id}`)
  }
}

export { referralApi }
