import request from './request'

const emergencyApi = {
  getList(params?: any) {
    return request.get('/v1/emergency/', { params })
  },
  getById(id: string) {
    return request.get(`/v1/emergency/${id}`)
  },
  create(data: any) {
    return request.post('/v1/emergency/', data)
  },
  update(id: string, data: any) {
    return request.put(`/v1/emergency/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/v1/emergency/${id}`)
  },
  // 处理急救记录
  processRecord(id: string, data: any) {
    return request.put(`/v1/emergency/${id}`, { ...data, status: 'processing' })
  },
  // 完成急救记录
  completeRecord(id: string, data: any) {
    return request.put(`/v1/emergency/${id}`, data).then(() => {
      return request.post(`/v1/emergency/${id}/complete`)
    })
  },
  // 取消急救记录
  cancelRecord(id: string, reason?: string) {
    return request.post(`/v1/emergency/${id}/cancel`, { cancel_reason: reason })
  }
}

export { emergencyApi }
