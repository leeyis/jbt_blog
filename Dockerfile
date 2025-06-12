# 使用Python 3.11 Alpine作为基础镜像
FROM python:3.11-alpine

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=jbt_blog.settings

# 安装系统依赖（编译某些Python包需要）
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    && rm -rf /var/cache/apk/*

# 复制requirements文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建静态文件目录
RUN mkdir -p staticfiles

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 执行数据库迁移
RUN python manage.py migrate

# 暴露端口
EXPOSE 8000

# 设置启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 