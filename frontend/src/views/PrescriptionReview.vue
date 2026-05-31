<template>
  <div class="page-container">
    <!-- 统计 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card"><el-statistic title="处方审核总数" :value="stats.total_reviews" /></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card"><el-statistic title="审核通过" :value="stats.approved" /></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card"><el-statistic title="调整优化" :value="stats.adjusted" /></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card"><el-statistic title="建议采纳率" :value="stats.adoption_rate" suffix="%" /></el-card>
      </el-col>
    </el-row>

    <!-- 审核列表 -->
    <el-card style="margin-top:16px">
      <template #header>
        <div class="card-header">
          <span>📝 处方审核记录</span>
          <div class="header-actions">
            <el-button type="warning" @click="showAiDialog = true" :icon="MagicStick" style="margin-right:8px">🤖 AI 智能推荐</el-button>
            <el-button type="success" @click="showManualDialog = true">📝 手动开方</el-button>
            <el-button type="primary" @click="showDialog = true">+ 新增审核</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="patient_name" label="患者" width="100" />
        <el-table-column prop="original_drug" label="原处方" min-width="150" />
        <el-table-column prop="original_dosage" label="原用量" width="100" />
        <el-table-column prop="suggested_drug" label="建议药品" min-width="150">
          <template #default="{ row }">
            <span :class="{ 'text-changed': row.suggested_drug !== row.original_drug }">{{ row.suggested_drug }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="suggested_dosage" label="建议用量" width="100" />
        <el-table-column label="审核结果" width="100">
          <template #default="{ row }">
            <el-tag :type="reviewResultTag(row.review_result)" size="small">{{ reviewResultLabel(row.review_result) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reviewer_name" label="审核人" width="100" />
        <el-table-column label="基层采纳" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_applied" type="success" size="small">已采纳</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="reviewed_at" label="审核时间" width="120" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="!row.is_applied && row.review_result !== 'REJECTED'" size="small" type="success" @click="apply(row.review_id)">采纳</el-button>
            <el-button size="small" type="warning" @click="sendWechat(row.review_id)">
              <el-icon><ChatDotRound /></el-icon> 发送微信
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top:16px; justify-content:center"
        @change="fetchList"
      />
    </el-card>

    <!-- 新增审核 -->
    <el-dialog v-model="showDialog" title="处方审核指导" width="560px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="患者ID" required><el-input v-model="form.patient_id" /></el-form-item>
        <el-form-item label="用药记录ID" required><el-input v-model="form.medication_id" /></el-form-item>
        <el-form-item label="建议用量"><el-input v-model="form.suggested_dosage" /></el-form-item>
        <el-form-item label="建议频次"><el-input v-model="form.suggested_frequency" /></el-form-item>
        <el-form-item label="建议用药"><el-input v-model="form.suggested_drug" /></el-form-item>
        <el-form-item label="审核理由"><el-input v-model="form.review_reason" type="textarea" rows="3" /></el-form-item>
        <el-form-item label="审核结果" required>
          <el-radio-group v-model="form.review_result">
            <el-radio-button value="APPROVED">通过</el-radio-button>
            <el-radio-button value="ADJUSTED">需调整</el-radio-button>
            <el-radio-button value="REJECTED">驳回</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="submit">提交审核</el-button>
      </template>
    </el-dialog>

    <!-- AI 智能推荐弹窗 -->
    <el-dialog v-model="showAiDialog" title="🤖 AI 处方智能推荐" width="680px" destroy-on-close @open="aiResult = null; aiPatientId = ''; aiLoading = false">
      <div v-if="!aiResult">
        <el-form label-width="100px">
          <el-form-item label="患者 ID">
            <el-input v-model="aiPatientId" placeholder="输入患者ID，如 P0001" @keyup.enter="runAiRecommend" />
          </el-form-item>
        </el-form>
        <div style="text-align:center; margin-top: 12px">
          <el-button type="warning" :loading="aiLoading" @click="runAiRecommend" size="large">
            🔍 开始智能分析
          </el-button>
        </div>
        <div class="ai-hint">AI 将分析患者当前用药、慢病类型、随访指标，给出用药建议和风险提示</div>
      </div>

      <div v-else v-loading="aiLoading">
        <!-- 总结 -->
        <el-alert :title="aiResult.summary" :type="aiResult.total_warnings > 0 ? 'warning' : 'success'" :closable="false" show-icon style="margin-bottom:16px" />

        <!-- 当前用药 -->
        <el-card v-if="aiResult.current_medications.length > 0" style="margin-bottom:12px">
          <template #header><span>💊 当前用药</span></template>
          <el-tag v-for="m in aiResult.current_medications" :key="m.medication_id" style="margin:4px" size="small">
            {{ m.drug_name }} {{ m.dosage }} {{ m.frequency }}
          </el-tag>
          <el-empty v-if="aiResult.current_medications.length === 0" description="无当前用药" :image-size="30" />
        </el-card>

        <!-- 用药建议 -->
        <el-card v-if="aiResult.recommendations.length > 0" style="margin-bottom:12px">
          <template #header><span>💡 用药建议 ({{ aiResult.recommendations.length }})</span></template>
          <div v-for="(r, i) in aiResult.recommendations" :key="i" class="ai-item rec">
            <div class="ai-item-header">
              <el-tag type="success" size="small">{{ r.disease_code }}</el-tag>
              <span style="margin-left:8px; font-weight:600">{{ r.drug_class }}</span>
              <span style="margin-left:auto; font-size:12px; color:#909399">置信度 {{ ((r.confidence || 0) * 100).toFixed(0) }}%</span>
            </div>
            <div class="ai-item-reason">{{ r.reason }}</div>
            <div class="ai-item-drugs">推荐药品：{{ (r.suggested_drugs || []).join('、') }}</div>
          </div>
        </el-card>

        <!-- 风险警告 -->
        <el-card v-if="aiResult.warnings.length > 0">
          <template #header><span>⚠️ 风险提示 ({{ aiResult.warnings.length }})</span></template>
          <div v-for="(w, i) in aiResult.warnings" :key="i" class="ai-item warn">
            <div class="ai-item-header">
              <el-tag :type="w.severity === 'HIGH' ? 'danger' : 'warning'" size="small">{{ w.severity }}</el-tag>
              <span style="margin-left:8px; font-weight:600">{{ w.type }}</span>
            </div>
            <div class="ai-item-reason">{{ w.message }}</div>
          </div>
        </el-card>

        <div style="text-align:center; margin-top:16px">
          <el-button @click="aiResult = null; aiPatientId = ''">重新分析</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 手动评估开方 -->
    <el-dialog v-model="showManualDialog" title="📝 医生手动评估开方" width="580px" destroy-on-close>
      <el-form :model="manualForm" label-width="100px">
        <el-form-item label="患者ID" required>
          <el-input v-model="manualForm.patient_id" placeholder="输入患者ID eg. p_0001" />
        </el-form-item>
        <el-form-item label="药品名称" required>
          <el-input v-model="manualForm.drug_name" placeholder="eg. 氨氯地平片" />
        </el-form-item>
        <el-form-item label="用量" required>
          <el-input v-model="manualForm.dosage" placeholder="eg. 5mg" />
        </el-form-item>
        <el-form-item label="频次" required>
          <el-select v-model="manualForm.frequency" placeholder="选择用药频次" style="width:100%">
            <el-option label="每日1次" value="每日1次" />
            <el-option label="每日2次" value="每日2次" />
            <el-option label="每日3次" value="每日3次" />
            <el-option label="每晚1次" value="每晚1次" />
            <el-option label="每8小时1次" value="每8小时1次" />
            <el-option label="每12小时1次" value="每12小时1次" />
            <el-option label="每周1次" value="每周1次" />
            <el-option label="必要时服用" value="必要时服用" />
          </el-select>
        </el-form-item>
        <el-form-item label="疗程">
          <el-input v-model="manualForm.duration" placeholder="eg. 30天 / 长期服用" />
        </el-form-item>
        <el-form-item label="评估理由">
          <el-input v-model="manualForm.review_reason" type="textarea" rows="2" placeholder="简述评估依据" />
        </el-form-item>
        <el-form-item label="医嘱备注">
          <el-input v-model="manualForm.notes" type="textarea" rows="2" placeholder="用药注意事项、饮食建议等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showManualDialog = false">取消</el-button>
        <el-button type="primary" @click="submitManual" :loading="manualSubmitting">确认开方</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { rxReviewApi, type RxReview, type RxReviewStats, type AIRecommendationResult } from '@/api/prescription-review';

const showAiDialog = ref(false);
const aiPatientId = ref('');
const aiLoading = ref(false);
const aiResult = ref<AIRecommendationResult | null>(null);

const loading = ref(false);
const list = ref<RxReview[]>([]);
const total = ref(0);
const currentPage = ref(1);
const showDialog = ref(false);
const showManualDialog = ref(false);
const manualSubmitting = ref(false);
const manualForm = reactive({
  patient_id: '', drug_name: '', dosage: '', frequency: '每日1次',
  duration: '', review_reason: '', notes: '',
});

const stats = reactive<RxReviewStats>({ total_reviews: 0, approved: 0, adjusted: 0, rejected: 0, applied_count: 0, adoption_rate: 0 });

const form = reactive({ patient_id: '', medication_id: '', suggested_dosage: '', suggested_frequency: '', suggested_drug: '', review_reason: '', review_result: 'APPROVED', notes: '' });

function reviewResultTag(r: string) { return r === 'APPROVED' ? 'success' : r === 'ADJUSTED' ? 'warning' : 'danger'; }
function reviewResultLabel(r: string) { return r === 'APPROVED' ? '通过' : r === 'ADJUSTED' ? '调整' : '驳回'; }

async function fetchList() {
  loading.value = true;
  try {
    const res = await rxReviewApi.list({ page: currentPage.value });
    list.value = res.items;
    total.value = res.total;
  } finally { loading.value = false; }
}

async function fetchStats() {
  const s = await rxReviewApi.stats();
  Object.assign(stats, s);
}

async function runAiRecommend() {
  if (!aiPatientId.value) { ElMessage.warning('请输入患者 ID'); return; }
  aiLoading.value = true;
  try {
    aiResult.value = await rxReviewApi.aiRecommend(aiPatientId.value);
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || 'AI 分析失败');
  } finally { aiLoading.value = false; }
}

async function submit() {
  try {
    await rxReviewApi.create(form);
    ElMessage.success('处方审核已提交');
    showDialog.value = false;
    fetchList(); fetchStats();
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '提交失败'); }
}

async function apply(reviewId: string) {
  try {
    await rxReviewApi.apply(reviewId);
    ElMessage.success('已采纳审核建议，处方已更新');
    fetchList(); fetchStats();
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '采纳失败'); }
}

async function submitManual() {
  if (!manualForm.patient_id || !manualForm.drug_name || !manualForm.dosage || !manualForm.frequency) {
    ElMessage.warning('请填写患者ID、药品名称、用量和频次');
    return;
  }
  manualSubmitting.value = true;
  try {
    const res = await rxReviewApi.manualAssess(manualForm);
    ElMessage.success('评估处方已创建！');
    showManualDialog.value = false;
    // 询问是否发送微信
    if (res.review_id) {
      try {
        await ElMessageBox.confirm('是否立即通过微信发送给患者？', '发送处方', {
          confirmButtonText: '发送', cancelButtonText: '稍后', type: 'info',
        });
        await rxReviewApi.sendWechat(res.review_id);
        ElMessage.success('处方已发送至患者微信 ✅');
      } catch { /* 用户选择稍后 */ }
    }
    fetchList(); fetchStats();
    // 重置表单
    Object.assign(manualForm, { patient_id: '', drug_name: '', dosage: '', frequency: '每日1次', duration: '', review_reason: '', notes: '' });
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.response?.data?.error || '开方失败');
  } finally { manualSubmitting.value = false; }
}

async function sendWechat(reviewId: string) {
  try {
    await ElMessageBox.confirm('确认通过微信发送该处方给患者？', '发送处方到微信', {
      confirmButtonText: '发送', type: 'warning',
    });
    await rxReviewApi.sendWechat(reviewId);
    ElMessage.success('处方已发送至患者微信 ✅');
    fetchList();
  } catch { /* 取消 */ }
}

onMounted(() => { fetchList(); fetchStats(); });
</script>

<style scoped>
.page-container { padding: 16px; }
.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-actions { display: flex; align-items: center; }
.text-changed { color: #E6A23C; font-weight: 600; }

/* AI Recommend */
.ai-hint { text-align: center; color: #909399; font-size: 13px; margin-top: 12px; }
.ai-item { padding: 10px 12px; margin-bottom: 8px; border-radius: 6px; }
.ai-item.rec { background: #f0f9eb; border-left: 3px solid #67C23A; }
.ai-item.warn { background: #fdf6ec; border-left: 3px solid #E6A23C; }
.ai-item-header { display: flex; align-items: center; margin-bottom: 4px; }
.ai-item-reason { font-size: 13px; color: #606266; line-height: 1.6; }
.ai-item-drugs { font-size: 12px; color: #1677FF; margin-top: 4px; }
</style>