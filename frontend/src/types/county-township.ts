// 县乡协同相关类型
export interface CountyHospital {
  name: string;
  code: string;
  totalPatients: number;
  activePatients: number;
  upReferrals: number;
  downReferrals: number;
  completionRate: number;
}

export interface TownshipClinic {
  name: string;
  code: string;
  totalPatients: number;
  activePatients: number;
  pendingReferrals: number;
  completedFollowups: number;
  lastMonthReferrals: number;
}

export interface ReferralFlow {
  totalUp: number;
  totalDown: number;
  avgResponseTime: number;
  timelyRate: number;
  monthlyTrend: MonthlyTrend[];
}

export interface MonthlyTrend {
  newMonth: string;
  upCount: number;
  downCount: number;
  completionRate: number;
}

export interface CollaborationStats {
  countyHospital: CountyHospital;
  townshipClinics: TownshipClinic[];
  referralFlow: ReferralFlow;
  collaborationScore: number;
}

export interface ResponseTimeRange {
  range: string;
  count: number;
}
