# 使用Python 3.11 Alpine作为基础镜像
FROM python:3.11-alpine

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=jbt_blog.settings

# 更换Alpine镜像源为阿里云镜像以提高下载速度和稳定性
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 安装系统依赖（编译psycopg2和其他Python包需要）
RUN apk update --no-cache && \
    apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    postgresql-dev \
    libpq \
    && rm -rf /var/cache/apk/*

# 升级pip并配置阿里云镜像源
RUN pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 复制requirements文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --timeout 60 \
    --retries 3 \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    -r requirements.txt

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
