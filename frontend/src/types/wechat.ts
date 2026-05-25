// 微信绑定类型定义（与后端 WechatResponse 对齐）
// 后端字段: wechat_id, patient_id, openid, nickname, avatar_url, bind_date, is_active, unbind_date, created_at

export interface WechatRecord {
  wechat_id?: string
  id?: string
  patient_id: string
  patient_name?: string
  openid: string
  nickname?: string
  avatar_url?: string
  bind_date?: string
  bind_status?: string
  is_active: boolean
  unbind_date?: string
  created_at?: string
}

export interface WechatBinding {
  id?: string
  wechat_id?: string
  patient_id: string
  patient_name?: string
  openid: string
  nickname?: string
  avatar_url?: string
  bind_date?: string
  bind_status?: string
  is_active: boolean
  unbind_date?: string
  created_at?: string
}

export interface WechatQuery {
  patient_id?: string
  bind_status?: string
  is_active?: boolean
  page?: number
  page_size?: number
}
