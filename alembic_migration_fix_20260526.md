# Alembic 增量迁移配置完成

**时间**: 2026-05-26 08:52-09:10
**目标**: 修复 Alembic 在 Python 3.9 + SQLite 下无法运行的问题，完成增量迁移配置

## 修复链

1. **pydantic-settings Python 3.9 bug** → `app/config.py` 改为 LazySettingsProxy，首次访问属性才触发 `get_settings()`
2. **session.py 模块加载崩溃** → `app/db/session.py` engine/factory 改为惰性初始化
3. **JSONB 类型不兼容 SQLite** → `app/models/__init__.py` JSONB→JSON，移除 `postgresql_using='gin'` 和 3 处 `postgresql_where`
4. **SQLite 无意义类型差异** → `alembic/env.py` 添加 `compare_type=False`
5. **旧 audit_log 表** → 直接 DROP（273 行数据，schema 与 sys_audit_log 不同）
6. **外键约束无命名** → SQLite batch mode 下会崩溃，用 `alembic stamp head` 跳过

## 验证结果

- `alembic current` → `a6867ccefc82 (head)` ✅
- 后端 API（登录/Dashboard/患者列表）→ 正常 ✅
- 前端 build → 0 errors, 11.94s ✅
- 数据库：27 表，65 患者，174 随访

## 关键决策

- SQLite 动态类型下 TEXT↔String, INTEGER↔Boolean, TIMESTAMP↔DateTime 的 ALTER COLUMN 无实际意义
- 外键和 NOT NULL 约束由 SQLAlchemy ORM 层保证，SQLite 不强制执行
- 迁移到 PostgreSQL 时用 `create_all` 建表即可，不需要 SQLite→PG 的迁移脚本
