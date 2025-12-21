FROM python:3.9-slim

WORKDIR /app

# 先复制依赖文件以利用构建缓存
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY backup_network_devices.py .
COPY app.py .
COPY devices.json .

# 设置并创建备份目录
ENV BACKUP_DIR=/app/backups
RUN mkdir -p /app/backups

# 暴露 Web 端口
EXPOSE 5000

# 启动脚本
COPY start.sh .
RUN chmod +x start.sh
CMD ["./start.sh"]