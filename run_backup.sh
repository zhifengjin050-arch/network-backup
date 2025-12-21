#!/bin/bash

# 设置备份目录
BACKUP_DIR="/app/backups"

# 设置日志文件
LOG_FILE="/var/log/backup_network_devices.log"

# 切换到项目目录
cd /home/osadmin/network-backup

# 确保备份目录存在
mkdir -p $BACKUP_DIR

# 执行备份脚本并记录日志
python3 backup_network_devices.py >> $LOG_FILE 2>&1

# 可选: 发送备份完成通知邮件
# echo "Backup completed on $(date)" | mail -s "Network Backup Completed" admin@example.com