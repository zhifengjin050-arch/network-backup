# 网络设备配置备份工具

这是一个用于自动备份华为网络设备配置的Python工具。它通过SSH连接到设备，执行`display saved-configuration`命令获取配置，并提供Web界面用于查看和下载备份文件。

## 功能

- 自动备份华为网络设备配置
- 支持多设备批量备份（多线程并发执行）
- 提供Web界面查看和下载备份文件
- 自动清理过期备份（默认保留90天）
- 支持Docker容器化部署

## 文件说明

- `backup_network_devices.py`: 主备份脚本
- `app.py`: Web界面应用
- `devices.json`: 设备配置文件
- `Dockerfile`: Docker构建文件
- `start.sh`: 容器启动脚本
- `requirements.txt`: Python依赖列表

## 使用方法

### 本地运行

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 配置设备:
   编辑`devices.json`文件，添加需要备份的设备信息。

3. 执行备份:
   ```bash
   python backup_network_devices.py
   ```

4. 启动Web服务:
   ```bash
   python app.py
   ```
   或使用启动脚本:
   ```bash
   ./start.sh
   ```
   默认情况下，Web服务将在 `http://localhost:5000` 上运行。

### Docker运行

1. 构建镜像:
   ```bash
   docker build -t network-backup .
   ```

2. 运行容器:
   ```bash
   docker run -d -p 5000:5000 -v /local/backup/path:/app/backups network-backup
   ```
   通过 `-v` 参数可以将容器内的备份目录挂载到宿主机，以实现持久化存储。

## 配置说明

### devices.json

设备配置文件，支持JSON格式和行尾注释(//)。

```json
{
  "devices": [
    {
      "hostname": "设备名称",
      "ip": "设备IP地址",
      "username": "SSH用户名",
      "password": "SSH密码",
      "device_type": "设备类型"  // 当前仅支持 "huawei"
    }
  ]
}
```

### 环境变量

- `BACKUP_DIR`: 备份文件存储目录，默认为 `/app/backups`