// 用户角色枚举
export enum UserRole {
  VILLAGE_DOCTOR = 'village_doctor',        // 村卫生室医生
  TOWNSHIP_DOCTOR = 'township_doctor',      // 乡镇卫生院医生
  COUNTY_DOCTOR = 'county_doctor',         // 县级医院医生
  ADMIN = 'admin'                         // 管理中心管理员
}

// 用户类型
export interface User {
  id: number
  username: string
  realName: string
  role: UserRole
  orgId: number
  orgName: string
  phone?: string
  avatar?: string
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应
export interface LoginResponse {
  accessToken: string
  tokenType: string
  user: User
}

// 疾病类型枚举
export enum DiseaseType {
  HYPERTENSION = 'hypertension',    // 高血压
  DIABETES = 'diabetes',            // 糖尿病
  CORONARY_HEART = 'coronary_heart',// 冠心病
  STROKE = 'stroke',               // 脑卒中
  COPD = 'copd',                   // COPD
  CKD = 'ckd'                      // 慢性肾病
}

// 患者基本信息
export interface Patient {
  id: number
  name: string
  idCard: string
  gender: 'male' | 'female'
  birthDate: string
  phone: string
  address: string
  villageId: number
  villageName: string
  townshipId: number
  townshipName: string
  diseases: DiseaseType[]
  createdAt: string
  updatedAt: string
}

// 患者列表查询参数
export interface PatientQueryParams {
  page: number
  pageSize: number
  keyword?: string
  diseaseType?: DiseaseType
  townshipId?: number
  villageId?: number
}

// 分页响应
export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

// 随访记录
export interface FollowUp {
  id: number
  patientId: number
  diseaseType: DiseaseType
  visitDate: string
  systolicBP?: number      // 收缩压
  diastolicBP?: number    // 舒张压
  heartRate?: number      // 心率
  weight?: number        // 体重
  height?: number        // 身高
  bmi?: number           // BMI
  symptoms?: string      // 症状
  medication?: string   // 用药情况
  compliance?: 'good' | 'fair' | 'poor'  // 依从性
  sideEffects?: string   // 不良反应
  nextVisitDate?: string// 下次随访日期
  riskScore?: number    // 风险评分
  doctorId: number
  doctorName: string
  remark?: string
}

// 随访表单查询参数
export interface FollowUpQueryParams {
  patientId: number
  diseaseType: DiseaseType
  page: number
  pageSize: number
}

// 随访表单数据（入参）
export interface FollowUpFormData {
  patientId: number
  diseaseType: DiseaseType
  visitDate: string
  systolicBP?: number
  diastolicBP?: number
  heartRate?: number
  weight?: number
  height?: number
  bmi?: number
  symptoms?: string
  medication?: string
  compliance?: 'good' | 'fair' | 'poor'
  sideEffects?: string
  nextVisitDate?: string
  riskScore?: number
  remark?: string
}

// 转诊类型
export enum ReferralType {
  UP = 'up',      // 上转（村->乡->县）
  DOWN = 'down'  // 下转（县->乡）
}

// 转诊状态
export enum ReferralStatus {
  PENDING = 'pending',      // 待审核
  APPROVED = 'approved',    // 已批准
  REJECTED = 'rejected',   // 已拒绝
  COMPLETED = 'completed', // 已完成
  CANCELLED = 'cancelled'  // 已取消
}

// 转诊记录
export interface Referral {
  id: number
  patientId: number
  patientName: string
  referralType: ReferralType
  fromOrgId: number
  fromOrgName: string
  toOrgId: number
  toOrgName: string
  reason: string
  diagnosis: string
  status: ReferralStatus
  rejectReason?: string
  createBy: number
  createByName: string
  createTime: string
  approveTime?: string
  completeTime?: string
}

// 转诊申请请求
export interface ReferralRequest {
  patientId: number
  referralType: ReferralType
  toOrgId: number
  reason: string
  diagnosis: string
}

// 机构类型
export enum OrgType {
  COUNTY = 'county',        // 县级
  TOWNSHIP = 'township',    // 乡镇
  VILLAGE = 'village'      // 村级
}

// 机构
export interface Organization {
  id: number
  name: string
  type: OrgType
  parentId?: number
}

// 预警类型
export enum AlertType {
  BP_ABNORMAL = 'bp_abnormal',      // 血压异常
  MISSING_FOLLOWUP = 'missing_followup', // 随访缺失
  RISK_HIGH = 'risk_high',          // 高风险
  MEDICATION_NONCOMPLIANCE = 'medication_noncompliance' // 用药依从性差
}

// 预警级别
export enum AlertLevel {
  INFO = 'info',       // 信息
  WARNING = 'warning', // 警告
  CRITICAL = 'critical' // 危急
}

// 预警记录
export interface Alert {
  id: number
  patientId: number
  patientName: string
  alertType: AlertType
  level: AlertLevel
  content: string
  relatedDisease?: DiseaseType
  isProcessed: boolean
  processTime?: string
  processBy?: number
  processByName?: string
  createTime: string
}

// KPI指标
export interface KpiMetric {
  name: string
  value: number
  target: number
  unit: string
  trend?: 'up' | 'down' | 'stable'
}

// 工作台统计数据
export interface DashboardStats {
  totalPatients: number
  hypertensionCount: number
  diabetesCount: number
  pendingFollowUps: number
  pendingReferrals: number
  unprocessedAlerts: number
  monthlyFollowUps: number
  monthlyNewPatients: number
  kpis: KpiMetric[]
}

// 中医体质类型
export enum TcmConstitution {
  YANG_DEFICIENCY = 'yang_deficiency',     // 阳虚质
  YIN_DEFICIENCY = 'yin_deficiency',     // 阴虚质
  PHLEGM_DAMP = 'phlegm_damp',           // 痰湿质
  HEAT_TOXIN = 'heat_toxin',             // 湿热质
  BLOOD_STASIS = 'blood_stasis',         // 血瘀质
  QI_DEFICIENCY = 'qi_deficiency',      // 气虚质
  QI_STAGNATION = 'qi_stagnation',       // 气郁质
  SPECIAL_CONSTITUTION = 'special'       // 特禀质
}

// 中医辨证记录
export interface TcmRecord {
  id: number
  patientId: number
  diseaseType: DiseaseType
  constitution: TcmConstitution
  syndromePattern: string
  tongueCoat: string
  pulseCondition: string
  herbalPrescription?: string
  herbalDosage?: string
  suitableTechnique?: string
  recordDate: string
  doctorId: number
  doctorName: string
}

// 年度评估报告
export interface AnnualAssessment {
  patientId: number
  year: number
  avgSystolicBP?: number
  avgDiastolicBP?: number
  avgBloodSugar?: number
  followUpCount: number
  controlAssessment: 'good' | 'fair' | 'poor'
  riskTrend: 'improving' | 'stable' | 'deteriorating'
  recommendations: string
  generateTime: string
}

// 急救联动记录
export interface EmergencyRecord {
  id: number
  patientId: number
  patientName: string
  emergencyType: 'stroke' | 'acs'
  triggerTime: string
  symptoms: string
  medicalHistory: string
  initialVitals: string
  hospitalId?: number
  hospitalName?: string
  admissionTime?: string
  outcome?: string
}

// 按钮权限
export interface Permission {
  code: string
  name: string
}

// 角色权限映射
export const RolePermissions: Record<UserRole, Permission[]> = {
  [UserRole.VILLAGE_DOCTOR]: [
    { code: 'followup:create', name: '随访录入' },
    { code: 'screening:view', name: '筛查' },
    { code: 'referral:up', name: '上转申请' }
  ],
  [UserRole.TOWNSHIP_DOCTOR]: [
    { code: 'patient:manage', name: '患者管理' },
    { code: 'referral:up', name: '上转申请' },
    { code: 'referral:down', name: '���转��收' },
    { code: 'report:basic', name: '基础报表' }
  ],
  [UserRole.COUNTY_DOCTOR]: [
    { code: 'diagnosis:adjust', name: '诊断调整' },
    { code: 'referral:down', name: '下转方案' },
    { code: 'treatment:review', name: '治疗方案审核' }
  ],
  [UserRole.ADMIN]: [
    { code: 'data:full', name: '全量数据' },
    { code: 'report:statistics', name: '考核统计' },
    { code: 'system:config', name: '系统配置' }
  ]
}