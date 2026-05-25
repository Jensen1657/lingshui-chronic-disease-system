# 陵水县人民医院慢病管理系统 - 后端 Dockerfile
# 简化版：无需编译工具链

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 配置 apt 国内镜像源（阿里云）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    (sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true)

# 仅安装运行时依赖（无需 build-essential）
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（使用阿里云 PyPI 镜像）
COPY requirements.txt ./
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 8000

# 启动命令
CMD ["gunicorn", "app.main:app", \
      "--workers", "2", \
      "--worker-class", "uvicorn.workers.UvicornWorker", \
      "--bind", "0.0.0.0:8000", \
      "--access-logfile", "-", \
      "--error-logfile", "-"]
