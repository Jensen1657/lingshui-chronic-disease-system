<template>
  <div class="page-container">
    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="📚 宣教模板" name="templates">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>宣教模板管理</span>
              <el-button type="primary" @click="showDialog = true; editing = false">+ 创建模板</el-button>
            </div>
          </template>

          <!-- 分类筛选 -->
          <el-radio-group v-model="activeCategory" @change="fetchTemplates" class="category-filter">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button v-for="c in categoryList" :key="c.code" :label="c.code">{{ c.name }}</el-radio-button>
          </el-radio-group>

      <!-- 模板卡片 -->
      <el-row :gutter="16" class="template-grid" v-loading="loading">
        <el-col v-for="t in templates" :key="t.template_id" :span="8" style="margin-bottom: 16px;">
          <el-card shadow="hover" class="template-card">
            <template #header>
              <div class="tpl-header">
                <span class="tpl-title">{{ t.title }}</span>
                <el-tag size="small" :type="t.is_active ? 'success' : 'info'">{{ t.is_active ? '启用' : '禁用' }}</el-tag>
              </div>
            </template>
            <p class="tpl-preview">{{ t.content_text?.substring(0, 100) }}...</p>
            <div class="tpl-meta">
              <el-tag size="small" effect="plain">{{ categoryName(t.category) }}</el-tag>
              <span class="usage">已推送 {{ t.usage_count }} 次</span>
            </div>
            <div class="tpl-actions">
              <el-button size="small" type="primary" @click="previewTemplate(t)">预览</el-button>
              <el-button size="small" @click="showSendDialog(t)">发送</el-button>
              <el-button size="small" type="info" @click="editTemplate(t)">编辑</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="!loading && templates.length === 0" description="暂无宣教模板" />

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: center"
        @change="fetchTemplates"
      />
      </el-card>
      </el-tab-pane>

      <!-- 推送效果统计 -->
      <el-tab-pane label="📊 推送效果" name="stats">
        <el-row :gutter="16" class="stats-row">
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="总推送量" :value="eduStats.total_sends" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="阅读率" :value="eduStats.read_rate" suffix="%" />
              <div class="stat-sub">已读 {{ eduStats.read_count }} 人</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="反馈率" :value="eduStats.feedback_rate" suffix="%" />
              <div class="stat-sub">已反馈 {{ eduStats.feedback_count }} 人</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <div class="stat-title">渠道分布</div>
              <div v-for="(count, ch) in eduStats.channel_stats" :key="ch" class="channel-item">
                <span class="ch-name">{{ channelLabel(ch) }}</span>
                <el-progress :percentage="round(count / eduStats.total_sends * 100)" :stroke-width="10" />
                <span class="ch-count">{{ count }}</span>
              </div>
              <el-empty v-if="!eduStats.channel_stats || Object.keys(eduStats.channel_stats).length === 0" description="暂无数据" :image-size="40" />
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="12">
            <el-card>
              <template #header><span>🔥 热门模板 TOP5</span></template>
              <el-table :data="eduStats.top_templates" stripe size="small">
                <el-table-column type="index" width="40" />
                <el-table-column prop="title" label="模板标题" min-width="160" />
                <el-table-column prop="category" label="分类" width="100">
                  <template #default="{ row }">{{ categoryName(row.category) }}</template>
                </el-table-column>
                <el-table-column prop="usage_count" label="推送次数" width="100" />
              </el-table>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header><span>📈 月度推送趋势</span></template>
              <div class="trend-chart">
                <div v-for="item in eduStats.monthly_trend" :key="item.month" class="trend-bar-wrap">
                  <div class="trend-label">{{ item.month.slice(5) }}</div>
                  <div class="trend-bar" :style="{ height: trendHeight(item.count) + 'px' }">
                    <span>{{ item.count }}</span>
                  </div>
                </div>
                <el-empty v-if="!eduStats.monthly_trend || eduStats.monthly_trend.length === 0" description="暂无数据" :image-size="40" />
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="24">
            <el-card>
              <template #header><span>📂 分类统计</span></template>
              <el-table :data="eduStats.category_stats" stripe size="small">
                <el-table-column prop="category" label="分类" width="120">
                  <template #default="{ row }">{{ categoryName(row.category) }}</template>
                </el-table-column>
                <el-table-column prop="template_count" label="模板数" width="100" />
                <el-table-column prop="usage_count" label="使用次数" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建/编辑模板弹窗 -->
    <el-dialog v-model="showDialog" :title="editing ? '编辑模板' : '创建宣教模板'" width="640px" destroy-on-close>
      <el-form :model="tplForm" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="tplForm.title" />
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="tplForm.category" style="width:100%">
            <el-option v-for="c in categoryList" :key="c.code" :label="c.name" :value="c.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用慢病">
          <el-select v-model="tplForm.disease_code" clearable style="width:100%">
            <el-option label="高血压" value="HYPERTENSION" />
            <el-option label="糖尿病" value="DIABETES" />
            <el-option label="冠心病" value="CHD" />
            <el-option label="脑卒中" value="STROKE" />
            <el-option label="慢阻肺" value="COPD" />
            <el-option label="慢性肾病" value="CKD" />
            <el-option label="通用" value="" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="tplForm.risk_level" clearable style="width:100%">
            <el-option label="低风险" value="LOW" />
            <el-option label="中风险" value="MEDIUM" />
            <el-option label="高风险" value="HIGH" />
            <el-option label="极高危" value="CRITICAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="正文内容" required>
          <el-input v-model="tplForm.content_text" type="textarea" rows="6" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="tagInput" placeholder="回车添加标签" @keyup.enter="addTag">
            <template #append><el-button @click="addTag">+</el-button></template>
          </el-input>
          <div style="margin-top:8px">
            <el-tag v-for="(t,i) in tplForm.tags" :key="i" closable @close="tplForm.tags!.splice(i,1)" style="margin-right:4px">
              {{ t }}
            </el-tag>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate">保存模板</el-button>
      </template>
    </el-dialog>

    <!-- 预览弹窗 -->
    <el-dialog v-model="previewVisible" title="模板预览" width="600px">
      <div class="preview-content">
        <h3>{{ previewData?.title }}</h3>
        <div style="white-space: pre-wrap; line-height: 1.8;">{{ previewData?.content_text }}</div>
      </div>
    </el-dialog>

    <!-- 发送弹窗 -->
    <el-dialog v-model="sendVisible" title="推送宣教内容" width="500px">
      <el-form label-width="100px">
        <el-form-item label="选择患者">
          <el-input v-model="sendPatientId" placeholder="输入患者ID" />
        </el-form-item>
        <el-form-item label="推送渠道">
          <el-radio-group v-model="sendChannel">
            <el-radio-button value="WECHAT">微信</el-radio-button>
            <el-radio-button value="SMS">短信</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sendVisible = false">取消</el-button>
        <el-button type="primary" @click="doSend">确认推送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { healthEduApi, type EduTemplate, type EduTemplateCreate, type HealthEduStats } from '@/api/health-education';

const activeTab = ref('templates');
const loading = ref(false);
const templates = ref<EduTemplate[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(9);
const activeCategory = ref('');
const categoryList = ref<{ code: string; name: string }[]>([]);

const showDialog = ref(false);
const editing = ref(false);
const tagInput = ref('');
const tplForm = reactive<EduTemplateCreate & { template_id?: string; tags?: string[] }>({
  title: '', category: 'DIET', disease_code: '', risk_level: '', content_text: '', tags: []
});

const previewVisible = ref(false);
const previewData = ref<EduTemplate | null>(null);

const sendVisible = ref(false);
const sendPatientId = ref('');
const sendChannel = ref('WECHAT');
const sendTarget = ref<EduTemplate | null>(null);

function categoryName(c: string) { const m = categoryList.value.find(x => x.code === c); return m?.name || c; }

// ========== 统计面板 ==========
const eduStats = reactive<HealthEduStats>({
  total_sends: 0, channel_stats: {}, read_rate: 0, read_count: 0,
  feedback_rate: 0, feedback_count: 0,
  monthly_trend: [], top_templates: [], category_stats: [],
});

const channelLabelMap: Record<string, string> = { WECHAT: '微信', SMS: '短信', APP: 'App', PRINT: '打印', MINI_APP: '小程序' };
function channelLabel(c: string) { return channelLabelMap[c] || c; }
function round(n: number) { return Math.round(n); }
function trendHeight(count: number) {
  const max = Math.max(...eduStats.monthly_trend.map(x => x.count), 1);
  return Math.max(Math.round(count / max * 180), 12);
}

async function fetchStats() {
  try {
    const s = await healthEduApi.stats();
    Object.assign(eduStats, s);
  } catch(e) { /* stats may not be critical */ }
}

function onTabChange(tab: string) {
  if (tab === 'stats') fetchStats();
}

// ========== 模板 ==========

async function fetchTemplates() {
  loading.value = true;
  try {
    const res = await healthEduApi.templates.list({
      page: currentPage.value, page_size: pageSize.value,
      category: activeCategory.value || undefined,
    });
    templates.value = res.items;
    total.value = res.total;
  } finally { loading.value = false; }
}

async function fetchCategories() {
  const res = await healthEduApi.categories();
  categoryList.value = res.categories;
}

function addTag() {
  const v = tagInput.value.trim();
  if (v && !tplForm.tags?.includes(v)) {
    if (!tplForm.tags) tplForm.tags = [];
    tplForm.tags.push(v);
  }
  tagInput.value = '';
}

function editTemplate(t: EduTemplate) {
  editing.value = true;
  Object.assign(tplForm, {
    template_id: t.template_id, title: t.title, category: t.category,
    disease_code: t.disease_code, risk_level: t.risk_level,
    content_text: t.content_text, tags: t.tags || [],
  });
  showDialog.value = true;
}

async function saveTemplate() {
  try {
    if (editing.value && tplForm.template_id) {
      await healthEduApi.templates.update(tplForm.template_id, {
        title: tplForm.title, category: tplForm.category,
        content_text: tplForm.content_text, tags: tplForm.tags,
        risk_level: tplForm.risk_level || undefined,
      });
      ElMessage.success('模板已更新');
    } else {
      await healthEduApi.templates.create({
        title: tplForm.title, category: tplForm.category,
        disease_code: tplForm.disease_code || undefined,
        risk_level: tplForm.risk_level || undefined,
        content_text: tplForm.content_text, tags: tplForm.tags,
      });
      ElMessage.success('模板已创建');
    }
    showDialog.value = false;
    editing.value = false;
    fetchTemplates();
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '保存失败'); }
}

function previewTemplate(t: EduTemplate) { previewData.value = t; previewVisible.value = true; }
function showSendDialog(t: EduTemplate) { sendTarget.value = t; sendVisible.value = true; }

async function doSend() {
  if (!sendPatientId.value || !sendTarget.value) { ElMessage.warning('请输入患者ID'); return; }
  try {
    await healthEduApi.send.one({
      patient_id: sendPatientId.value,
      template_id: sendTarget.value.template_id,
      sent_channel: sendChannel.value,
    });
    ElMessage.success('宣教内容已推送');
    sendVisible.value = false;
    sendPatientId.value = '';
    fetchTemplates();
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '推送失败'); }
}

onMounted(() => { fetchCategories(); fetchTemplates(); });
</script>

<style scoped>
.page-container { padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.category-filter { margin-bottom: 20px; }
.template-card { height: 240px; display: flex; flex-direction: column; }
.tpl-header { display: flex; justify-content: space-between; align-items: center; }
.tpl-title { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; margin-right: 8px; }
.tpl-preview { color: #666; font-size: 13px; line-height: 1.6; flex: 1; }
.tpl-meta { display: flex; justify-content: space-between; align-items: center; margin: 8px 0; }
.usage { color: #999; font-size: 12px; }
.tpl-actions { display: flex; gap: 8px; }
.preview-content { padding: 16px; }

/* Stats */
.stats-row { margin-bottom: 8px; }
.stat-card { text-align: center; }
.stat-card .stat-title { font-size: 13px; color: #909399; margin-bottom: 8px; }
.stat-card .stat-sub { font-size: 12px; color: #909399; margin-top: 4px; }
.channel-item { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.channel-item .ch-name { width: 40px; font-size: 12px; color: #606266; text-align: right; }
.channel-item .el-progress { flex: 1; }
.channel-item .ch-count { width: 30px; font-size: 12px; color: #909399; }
.trend-chart { display: flex; align-items: flex-end; gap: 12px; padding: 8px 0; min-height: 220px; }
.trend-bar-wrap { display: flex; flex-direction: column; align-items: center; flex: 1; }
.trend-label { font-size: 11px; color: #909399; margin-bottom: 4px; }
.trend-bar { width: 100%; max-width: 36px; background: linear-gradient(to top, #409EFF, #79BBFF); border-radius: 4px 4px 0 0; display: flex; align-items: flex-start; justify-content: center; min-width: 20px; }
.trend-bar span { font-size: 11px; color: #fff; padding-top: 2px; }
</style>