<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>💊 患者用药记录</span>
          <el-button type="primary" @click="showDialog = true">+ 录入用药</el-button>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="16" class="stats-row">
        <el-col :span="6">
          <el-statistic title="用药总人数" :value="totalMedications" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="长期用药" :value="longTermCount" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="依从率" :value="adherenceRate" suffix="%" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="已停药" :value="inactiveCount" />
        </el-col>
      </el-row>

      <!-- 筛选 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="患者姓名">
          <el-input v-model="filters.patientSearch" placeholder="搜索姓名" clearable style="width:160px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="药品名称">
          <el-input v-model="filters.drugName" placeholder="药品名" clearable style="width:160px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.isActive" clearable style="width:120px">
            <el-option label="在用" :value="true" />
            <el-option label="已停" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="patient_name" label="患者" width="100" />
        <el-table-column prop="drug_name" label="药品名称" min-width="150" />
        <el-table-column prop="dosage" label="用量" width="100" />
        <el-table-column prop="frequency" label="频次" width="80" />
        <el-table-column prop="start_date" label="开始日期" width="110" />
        <el-table-column label="依从性" width="100">
          <template #default="{ row }">
            <el-tag :type="adherenceTag(row.adherence_status)" size="small">
              {{ adherenceLabel(row.adherence_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '在用' : '停药' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
            <el-button size="small" type="warning" @click="editMed(row)">调整</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @change="fetchData"
      />
    </el-card>

    <!-- 录入/编辑弹窗 -->
    <el-dialog v-model="showDialog" :title="editing ? '调整用药' : '录入用药记录'" width="560px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="患者ID" required>
          <el-input v-model="form.patient_id" :disabled="editing" />
        </el-form-item>
        <el-form-item label="药品名称" required>
          <el-input v-model="form.drug_name" />
        </el-form-item>
        <el-form-item label="药品类别">
          <el-input v-model="form.drug_class" placeholder="如 ARB类/他汀类" />
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="form.specification" placeholder="如 30mg" />
        </el-form-item>
        <el-form-item label="用量" required>
          <el-input v-model="form.dosage" />
        </el-form-item>
        <el-form-item label="频次" required>
          <el-select v-model="form.frequency" style="width:100%">
            <el-option label="每日一次(qd)" value="qd" />
            <el-option label="每日两次(bid)" value="bid" />
            <el-option label="每日三次(tid)" value="tid" />
            <el-option label="睡前(qn)" value="qn" />
            <el-option label="必要时(prn)" value="prn" />
          </el-select>
        </el-form-item>
        <el-form-item label="给药途径">
          <el-select v-model="form.route" style="width:100%">
            <el-option label="口服" value="口服" />
            <el-option label="吸入" value="吸入" />
            <el-option label="外用" value="外用" />
            <el-option label="注射" value="注射" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期" required>
          <el-date-picker v-model="form.start_date" type="date" style="width:100%" />
        </el-form-item>
        <el-form-item label="长期用药">
          <el-switch v-model="form.is_long_term" />
        </el-form-item>
        <el-form-item v-if="editing" label="依从性">
          <el-select v-model="form.adherence_status" style="width:100%">
            <el-option label="良好" value="GOOD" />
            <el-option label="部分" value="PARTIAL" />
            <el-option label="不佳" value="POOR" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editing" label="副作用">
          <el-input v-model="form.side_effects" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { medicationApi, type MedicationItem, type MedicationCreate } from '@/api/medication';

const loading = ref(false);
const items = ref<MedicationItem[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const showDialog = ref(false);
const editing = ref(false);
const totalMedications = ref(0);
const longTermCount = ref(0);
const inactiveCount = ref(0);
const adherenceRate = ref(0);

const filters = reactive({ patientSearch: '', drugName: '', isActive: undefined as boolean | undefined });

const form = reactive<MedicationCreate & { medication_id?: string; adherence_status?: string; side_effects?: string; is_long_term?: boolean; route?: string }>({
  patient_id: '', disease_code: 'HYPERTENSION', drug_name: '', drug_class: '', specification: '', dosage: '', frequency: 'qd', route: '口服', start_date: '', is_long_term: true, notes: ''
});

const adherenceTag = (s: string) => s === 'GOOD' ? 'success' : s === 'PARTIAL' ? 'warning' : s === 'POOR' ? 'danger' : 'info';
const adherenceLabel = (s: string) => s === 'GOOD' ? '良好' : s === 'PARTIAL' ? '部分' : s === 'POOR' ? '不佳' : '未知';

async function fetchData() {
  loading.value = true;
  try {
    const params: Record<string, unknown> = { page: currentPage.value, page_size: pageSize.value };
    if (filters.drugName) params.drug_name = filters.drugName;
    if (filters.isActive !== undefined) params.is_active = filters.isActive;
    const res = await medicationApi.list(params as any);
    items.value = res.items;
    total.value = res.total;
    // Update stats
    totalMedications.value = res.total;
    longTermCount.value = res.items.filter((i: MedicationItem) => i.is_long_term && i.is_active).length;
    inactiveCount.value = res.items.filter((i: MedicationItem) => !i.is_active).length;
    const goodCount = res.items.filter((i: MedicationItem) => i.adherence_status === 'GOOD').length;
    adherenceRate.value = res.total > 0 ? Math.round(goodCount / res.total * 100) : 0;
  } finally {
    loading.value = false;
  }
}

function search() { currentPage.value = 1; fetchData(); }

function viewDetail(row: MedicationItem) {
  ElMessage.info(`药品详情: ${row.drug_name} ${row.dosage} ${row.frequency}`);
}

function editMed(row: MedicationItem) {
  editing.value = true;
  Object.assign(form, {
    medication_id: row.medication_id,
    patient_id: row.patient_id,
    disease_code: row.disease_code,
    drug_name: row.drug_name,
    drug_class: row.drug_class || '',
    specification: row.specification || '',
    dosage: row.dosage,
    frequency: row.frequency,
    route: row.route || '口服',
    start_date: row.start_date,
    is_long_term: row.is_long_term,
    adherence_status: row.adherence_status || '',
    side_effects: row.side_effects || '',
    notes: row.notes || '',
  });
  showDialog.value = true;
}

async function submit() {
  try {
    if (editing.value && form.medication_id) {
      await medicationApi.update(form.medication_id, {
        dosage: form.dosage,
        frequency: form.frequency,
        route: form.route,
        adherence_status: form.adherence_status,
        side_effects: form.side_effects,
        notes: form.notes,
      });
      ElMessage.success('用药调整已保存');
    } else {
      await medicationApi.create({
        patient_id: form.patient_id,
        disease_code: form.disease_code,
        drug_name: form.drug_name,
        drug_class: form.drug_class || undefined,
        specification: form.specification || undefined,
        dosage: form.dosage,
        frequency: form.frequency,
        route: form.route,
        start_date: form.start_date,
        is_long_term: form.is_long_term,
        notes: form.notes || undefined,
      });
      ElMessage.success('用药记录已保存');
    }
    showDialog.value = false;
    editing.value = false;
    fetchData();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败');
  }
}

onMounted(fetchData);
</script>

<style scoped>
.page-container { padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.stats-row { margin-bottom: 20px; }
.filter-form { margin-top: 16px; }
</style>