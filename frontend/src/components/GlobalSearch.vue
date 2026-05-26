<template>
  <div class="global-search" ref="searchContainer">
    <el-input
      v-model="searchKeyword"
      placeholder="搜索患者（姓名/ID/手机号）"
      prefix-icon="Search"
      clearable
      @input="handleSearch"
      @clear="closeDropdown"
      @focus="showDropdown = true"
      class="search-input"
    />
    
    <!-- 搜索结果下拉框 -->
    <div v-if="showDropdown && searchResults.length > 0" class="search-dropdown">
      <div
        v-for="patient in searchResults"
        :key="patient.patient_id"
        class="search-item"
        @click="goToPatient(patient)"
      >
        <div class="patient-info">
          <span class="patient-name">{{ patient.name || patient.name_enc }}</span>
          <el-tag size="small" :type="patient.gender === 'M' ? '' : 'danger'">
            {{ patient.gender === 'M' ? '男' : '女' }}
          </el-tag>
        </div>
        <div class="patient-meta">
          <span>ID: {{ patient.patient_id }}</span>
          <span v-if="patient.phone || patient.phone_enc">📞 {{ patient.phone || patient.phone_enc }}</span>
        </div>
      </div>
      
      <div v-if="searchResults.length >= 10" class="search-more">
        仅显示前 10 条结果，请缩小搜索范围
      </div>
    </div>
    
    <!-- 无结果提示 -->
    <div v-if="showDropdown && hasSearched && searchResults.length === 0 && searchKeyword.trim()" class="search-dropdown search-empty">
      未找到匹配的患者
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const searchContainer = ref<HTMLElement | null>(null)
const searchKeyword = ref('')
const searchResults = ref<any[]>([])
const showDropdown = ref(false)
const hasSearched = ref(false)
let searchTimer: number | null = null

const handleSearch = () => {
  // 防抖处理
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    closeDropdown()
    return
  }
  
  searchTimer = setTimeout(async () => {
    try {
      hasSearched.value = true
      showDropdown.value = true
      
      const response = await fetch(
        `/api/v1/patients/?search=${encodeURIComponent(keyword)}&limit=10`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      )
      
      if (!response.ok) {
        throw new Error('搜索失败')
      }
      
      const data = await response.json()
      searchResults.value = data.items || []
    } catch (error: any) {
      console.error('搜索失败:', error)
      searchResults.value = []
    }
  }, 300)
}

const closeDropdown = () => {
  showDropdown.value = false
  hasSearched.value = false
}

const goToPatient = (patient: any) => {
  closeDropdown()
  searchKeyword.value = ''
  router.push(`/patients/${patient.patient_id}`)
}

// 点击外部关闭下拉框
const handleClickOutside = (event: MouseEvent) => {
  if (searchContainer.value && !searchContainer.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.global-search {
  position: relative;
  width: 400px;
  margin: 0 20px;
}

.search-input {
  width: 100%;
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  max-height: 400px;
  overflow-y: auto;
  z-index: 2000;
}

.search-item {
  padding: 10px 15px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.search-item:last-child {
  border-bottom: none;
}

.search-item:hover {
  background: #f5f7fa;
}

.patient-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.patient-name {
  font-weight: 600;
  font-size: 14px;
}

.patient-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #909399;
}

.search-empty {
  padding: 20px;
  text-align: center;
  color: #909399;
}

.search-more {
  padding: 8px;
  text-align: center;
  font-size: 12px;
  color: #909399;
  background: #fafafa;
}
</style>
