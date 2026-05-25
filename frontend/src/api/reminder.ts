import request from './request'

const reminderApi = {
  getList(params?: any) {
    return request.get('/v1/reminders/', { params })
  },
  getById(id: string) {
    return request.get(`/v1/reminders/${id}`)
  },
  create(data: any) {
    return request.post('/v1/reminders/', data)
  },
  update(id: string, data: any) {
    return request.put(`/v1/reminders/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/v1/reminders/${id}`)
  }
}

export { reminderApi }
