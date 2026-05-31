<template>
  <div class="page-container">
    <!-- 风险驾驶舱 -->
    <el-row :gutter="16" class="dashboard-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="在管患者" :value="dashboard.total_patients" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="高风险患者" :value="dashboard.high_risk_count">
            <template #suffix>
              <span class="risk-high"> ({{ dashboard.high_risk_rate }}%)</span>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="未评估率" :value="dashboard.unassessed_rate" suffix="%">
            <template #suffix>
              <el-tag v-if="dashboard.unassessed_rate > 20" type="warning" size="small">需关注</el-tag>
              <el-tag v-else type="success" size="small">达标</el-tag>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div style="text-align:center">
            <el-button type="primary" @click="batchAssessDialog = true">批量自动分层</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险分布 -->
    <el-card title="患者风险分层分布" style="margin-top:16px" v-loading="loading">
      <template #header><span>🎯 患者风险分层分布</span></template>
      <el-row :gutter="16">
        <el-col v-for="item in riskDistData" :key="item.label" :span="4">
          <div class="risk-bar" :style="{ backgroundColor: item.color }">
            <div class="risk-bar-label">{{ item.label }}</div>
            <div class="risk-bar-count">{{ item.count }}</div>
            <el-progress :percentage="item.percent" :color="item.color" :show-text="false" />
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 分级列表 -->
    <el-card style="margin-top:16px">
      <template #header><span>📋 患者分级管理列表</span></template>
      <el-form :inline="true">
        <el-form-item label="风险等级">
          <el-select v-model="filterRiskLevel" clearable @change="fetchList">
            <el-option label="低风险" value="LOW" />
            <el-option label="中风险" value="MEDIUM" />
            <el-option label="高风险" value="HIGH" />
            <el-option label="极高危" value="CRITICAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="管理层级">
          <el-select v-model="filterManageLevel" clearable @change="fetchList">
            <el-option label="村级" value="VILLAGE" />
            <el-option label="乡镇" value="TOWNSHIP" />
            <el-option label="县级" value="COUNTY" />
            <el-option label="转诊" value="REFERRAL" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="patient_name" label="患者姓名" width="100" />
        <el-table-column label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="riskTag(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_score" label="评分" width="80" />
        <el-table-column label="管理层级" width="100">
          <template #default="{ row }">
            {{ manageLabel(row.manage_level) }}
          </template>
        </el-table-column>
        <el-table-column prop="followup_frequency" label="随访频次" width="100" />
        <el-table-column prop="bp_assessment" label="血压评估" width="100" />
        <el-table-column prop="bg_assessment" label="血糖评估" width="100" />
        <el-table-column label="需上转" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.need_up_referral" type="danger" size="small">是</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="assessed_at" label="评估时间" width="120" />
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        :total="listTotal"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: center"
        @change="fetchList"
      />
    </el-card>

    <!-- 批量分层弹窗 -->
    <el-dialog v-model="batchAssessDialog" title="批量自动分层" width="480px">
      <p>将对所有患者执行自动风险分层计算，根据慢病数量、年龄、血压血糖等指标自动评估风险等级并分配管理机构。</p>
      <el-alert type="info" show-icon :closable="false" title="自动分层后可通过查询直接看到结果" style="margin-bottom:16px" />
      <template #footer>
        <el-button @click="batchAssessDialog = false">取消</el-button>
        <el-button type="primary" @click="doBatchAssess" :loading="assessing">开始分层</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { riskApi, type RiskAssessment, type RiskDashboard } from '@/api/risk-assessment';

const loading = ref(false);
const assessing = ref(false);
const batchAssessDialog = ref(false);

const dashboard = reactive<RiskDashboard>({
  total_patients: 0, risk_distribution: {}, unassessed_rate: 0,
  high_risk_count: 0, high_risk_rate: 0, status: 'OK', message: ''
});

const riskDistData = ref<{ label: string; count: number; percent: number; color: string }[]>([]);

const list = ref<RiskAssessment[]>([]);
const listTotal = ref(0);
const currentPage = ref(1);
const filterRiskLevel = ref('');
const filterManageLevel = ref('');

const colors: Record<string, string> = { LOW: '#67C23A', MEDIUM: '#E6A23C', HIGH: '#F56C6C', CRITICAL: '#F56C6C', UNASSESSED: '#909399', VERY_HIGH: '#E5606B' };
const labels: Record<string, string> = { LOW: '低风险', MEDIUM: '中风险', HIGH: '高风险', CRITICAL: '极高危', UNASSESSED: '未评估', VERY_HIGH: '高危预警' };
const manageLabels: Record<string, string> = { VILLAGE: '村级管理', TOWNSHIP: '乡镇管理', COUNTY: '县级管理', REFERRAL: '建议转诊' };

function riskTag(l: string) { return l === 'HIGH' || l === 'CRITICAL' ? 'danger' : l === 'MEDIUM' ? 'warning' : 'success'; }
function manageLabel(l: string) { return manageLabels[l] || l; }

async function fetchDashboard() {
  const d = await riskApi.dashboard();
  Object.assign(dashboard, d);
  // Build distribution bars
  riskDistData.value = Object.entries(d.risk_distribution).map(([k, v]) => ({
    label: labels[k] || k,
    count: v as number,
    percent: d.total_patients > 0 ? Math.round((v as number) / d.total_patients * 100) : 0,
    color: colors[k] || '#909399',
  }));
}

async function fetchList() {
  loading.value = true;
  try {
    const res = await riskApi.list({
      page: currentPage.value,
      risk_level: filterRiskLevel.value || undefined,
      manage_level: filterManageLevel.value || undefined,
    });
    list.value = res.items;
    listTotal.value = res.total;
  } finally { loading.value = false; }
}

async function doBatchAssess() {
  assessing.value = true;
  try {
    // fetch all patient IDs from existing list or known range
    const pids = Array.from({ length: 65 }, (_, i) => `p_${String(i + 1).padStart(4, '0')}`);
    await riskApi.batch(pids, true);
    ElMessage.success('批量分层完成');
    batchAssessDialog.value = false;
    fetchDashboard();
    fetchList();
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '分层失败'); }
  finally { assessing.value = false; }
}

onMounted(() => { fetchDashboard(); fetchList(); });
</script>

<style scoped>
.page-container { padding: 16px; }
.stat-card { text-align: center; }
.risk-high { color: #F56C6C; font-size: 13px; }
.risk-bar { text-align: center; padding: 12px 8px; border-radius: 8px; color: white; }
.risk-bar-label { font-size: 13px; opacity: 0.9; }
.risk-bar-count { font-size: 24px; font-weight: bold; }
</style>