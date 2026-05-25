<template>
  <div class="assessment-detail">
    <el-page-header @back="goBack" title="返回列表">
      <template #content>
        <span class="text-large font-600 mr-3"> 评估详情 </span>
      </template>
    </el-page-header>

    <el-alert v-if="notFound" title="评估记录不存在" type="error" show-icon :closable="false" style="margin-top: 16px;" />

    <el-card class="mt-4" v-loading="loading" v-if="!notFound">
      <template #header>
        <div class="card-header">
          <span>评估信息</span>
          <el-tag :type="getRiskLevelType(record?.risk_level)">{{ getRiskLevelText(record?.risk_level) }}</el-tag>
        </div>
      </template>

      <el-descriptions :column="2" border v-if="record">
        <el-descriptions-item label="评估ID">{{ record.id }}</el-descriptions-item>
        <el-descriptions-item label="患者ID">{{ record.patient_id }}</el-descriptions-item>
        <el-descriptions-item label="评估年份">{{ record.assessment_year }}</el-descriptions-item>
        <el-descriptions-item label="BMI">{{ record.bmi }}</el-descriptions-item>
        <el-descriptions-item label="风险等级">
          <el-tag :type="getRiskLevelType(record.risk_level)">{{ getRiskLevelText(record.risk_level) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="评估得分">{{ record.score }}</el-descriptions-item>
        <el-descriptions-item label="评估日期">{{ formatDate(record.assessment_date) }}</el-descriptions-item>
        <el-descriptions-item label="下次评估日期">{{ formatDate(record.next_assessment_date) }}</el-descriptions-item>
        <el-descriptions-item label="评估医生">{{ record.doctor_name }}</el-descriptions-item>
        <el-descriptions-item label="评估机构">{{ record.organization_name }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ record.remarks }}</el-descriptions-item>
      </el-descriptions>

      <el-empty v-else description="暂无数据" />
    </el-card>

    <div class="actions mt-4" v-if="record">
      <el-button type="primary" @click="handleEdit">编辑</el-button>
      <el-button type="danger" @click="handleDelete">删除</el-button>
      <el-button @click="goBack">返回</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAssessmentStore } from '@/stores/assessment';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { Assessment } from '@/types/assessment';

const route = useRoute();
const router = useRouter();
const store = useAssessmentStore();

const loading = ref(false);
const notFound = ref(false);
const record = ref<Assessment | null>(null);

const getRiskLevelType = (riskLevel: string | undefined) => {
  if (!riskLevel) return 'info';
  switch (riskLevel.toLowerCase()) {
    case 'low':
    case '低危':
      return 'success';
    case 'medium':
    case '中危':
      return 'warning';
    case 'high':
    case '高危':
      return 'danger';
    default:
      return 'info';
  }
};

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('zh-CN');
};

const fetchRecord = async () => {
  const id = route.params.id as string;
  if (!id) {
    ElMessage.error('评估ID不存在');
    return;
  }

  loading.value = true;
  notFound.value = false;
  try {
    const result = await store.getById(id);
    record.value = result;
  } catch (error: any) {
    if (error?.response?.status === 404 || error?.status === 404) {
      notFound.value = true;
    } else {
      ElMessage.error(error.message || '获取评估详情失败');
    }
  } finally {
    loading.value = false;
  }
};

const handleEdit = () => {
  const id = route.params.id as string;
  router.push({ name: 'AssessmentEdit', params: { id } });
};

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这条评估记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });

    const id = route.params.id as string;
    await store.deleteAssessment(id);
    ElMessage.success('删除成功');
    goBack();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败');
    }
  }
};

const goBack = () => {
  router.push({ name: 'AssessmentList' });
};

onMounted(() => {
  fetchRecord();
});
</script>

<style scoped>
.assessment-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mt-4 {
  margin-top: 16px;
}

.actions {
  display: flex;
  gap: 10px;
}
</style>