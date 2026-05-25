import request from './request'

const wechatApi = {
  getList(params?: any) {
    return request.get('/v1/wechat/', { params })
  },
  getById(id: string) {
    return request.get(`/v1/wechat/${id}`)
  },
  create(data: any) {
    return request.post('/v1/wechat/', data)
  },
  update(id: string, data: any) {
    return request.put(`/v1/wechat/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/v1/wechat/${id}`)
  },
  // 解绑微信
  unbind(id: string) {
    return request.post(`/v1/wechat/${id}/unbind`)
  },
  // 发送通知（后端暂未实现，先保留接口）
  sendNotification(id: string, data: any) {
    return request.post(`/v1/wechat/${id}/notify`, data)
  }
}

export { wechatApi }
