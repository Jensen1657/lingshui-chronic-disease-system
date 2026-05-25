<template>
  <div class="table-skeleton">
    <div v-for="i in rows" :key="i" class="skeleton-row">
      <el-skeleton :rows="1" animated />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  rows?: number
}>()
</script>

<style scoped>
.table-skeleton {
  padding: 16px 20px;
}
.skeleton-row {
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}
.skeleton-row:last-child {
  border-bottom: none;
}
</style>
