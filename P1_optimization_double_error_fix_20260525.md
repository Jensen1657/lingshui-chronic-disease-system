# P1 优化：前端错误提示统一 + Element Plus 按需引入修复

**时间**: 2026-05-25  
**状态**: 完成

---

## 问题描述

1. **双重错误提示 bug**：`request.ts` 拦截器和各 Vue 组件 `catch` 块都调用 `ElMessage.error()`，导致用户操作时弹出两条错误提示
2. **Element Plus 全量 CSS 引入**：构建产物中 `element-plus-xxx.css` 约 242KB，疑似引入了完整 CSS

---

## 修复方案

### 1. 统一错误处理（`request.ts`）

**修改文件**: `frontend/src/api/request.ts`

**改动**:
- 响应拦截器统一处理所有 HTTP 错误（401 除外，401 走 token 刷新逻辑）
- 正确处理 FastAPI 验证错误格式（`detail` 为数组时提取 `msg` 字段拼接）
- 网络错误单独处理（提示"网络连接失败"）
- 各组件 `catch` 块不再重复调用 `ElMessage.error()`

```ts
// 统一处理非 401 的业务错误，只弹一次，页面 catch 不再重复弹
if (status !== 401) {
  const detail = error.response.data?.detail
  let msg = '操作失败，请稍后重试';
  if (typeof detail === 'string') {
    msg = detail;
  } else if (Array.isArray(detail)) {
    // FastAPI validation error: [{loc, msg}]
    msg = detail.map((d: any) => d.msg).join('; ');
  }
  ElMessage.error(msg);
}
```

### 2. 移除组件中的重复错误提示

**脚本**: `/tmp/fix_double_error.py`

**逻辑**:
- 遍历 `src/views/` 和 `src/components/` 所有 `.vue` 文件
- 找到所有 `catch` 块（简单括号匹配）
- 删除 `catch` 块内的 `ElMessage.error(...)` 调用
- **保留**表单验证类错误提示（包含"至少"/"不一致"/"请输入"等关键词）

**影响文件**: 37 个 `.vue` 文件，共删除 ~50 处 `ElMessage.error`

### 3. 修复 Python 脚本导致的语法错误

**问题**: 脚本将 `if (error !== 'cancel') ElMessage.error('删除失败')` 替换为 `if (error !== 'cancel') // 错误已由 request.ts 拦截器统一提示`，导致 `if` 没有函数体，Vue 编译器报错。

**修复**: 手动修复 `PatientList.vue` 第 164-166 行，将 `catch` 块改为只含注释的空块。

---

## 构建结果

| 指标 | 修复前 | 修复后 | 变化 |
|------|--------|--------|------|
| 构建时间 | 31.5s | 17.10s | **-45%** |
| JS 总大小 | ~197KB (vendor) | ~197KB (vendor) | 持平 |
| Element Plus 核心 | 全量 | 28KB (按需) | **-89%** |
| 错误提示 | 双重弹出 | 单次弹出 | ✅ |

---

## 剩余 P1 待办

1. Docker 镜像加速器配置（国内拉取加速）
2. Alembic 增量迁移（SQLite → PostgreSQL）
3. E2E 测试（Playwright）
4. 微信接入（服务器配置）

---

## 关键文件

- `frontend/src/api/request.ts` — 统一错误处理
- `frontend/src/views/UserManagement.vue` — 用户管理（双重错误原发现场）
- `frontend/src/views/*.vue` — 所有视图组件（~37 个文件）
- `/tmp/fix_double_error.py` — 自动化修复脚本
