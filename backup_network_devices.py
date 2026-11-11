import paramiko
import time
import os
import json
import re
import logging
import datetime
import requests
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# ==========================================
# 🔧 用户配置区域
# ==========================================

# 1. 钉钉 Webhook 地址
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK_URL", "").strip()
# 2. 你的服务器 IP 地址
SERVER_IP = "192.172.77.3"
SERVER_PORT = "5000"

# ==========================================

# 定义北京时区 (UTC+8)
BJ_TZ = datetime.timezone(datetime.timedelta(hours=8))

# 全局变量
BACKUP_DIR = os.getenv('BACKUP_DIR', './backups')
DEVICE_FILE = os.getenv('DEVICE_FILE', 'devices.json')
RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', 90))
MAX_WORKERS = int(os.getenv('MAX_WORKERS', 10))

def load_devices():
    """读取带有注释的JSON配置文件"""
    try:
        with open(DEVICE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            content = re.sub(r'//.*', '', content)
            return json.loads(content)
    except Exception as e:
        logging.error(f"读取设备文件失败: {e}")
        return {"devices": []}

def send_dingtalk_alert(success_count, fail_count, failed_devices, duration):
    """发送美化版的钉钉告警"""
    if not DINGTALK_WEBHOOK or "你的Token" in DINGTALK_WEBHOOK:
        logging.warning("未配置钉钉Webhook，跳过发送通知")
        return

    # 构造Web管理界面的链接
    web_url = f"http://{SERVER_IP}:{SERVER_PORT}"
    
    # 构造当前时间 (强制使用北京时间)
    current_time = datetime.datetime.now(BJ_TZ).strftime('%Y-%m-%d %H:%M:%S')

    # 构造Markdown消息内容
    title = "🛡️ 浙江强脑科技有限公司网络设备备份周报"
    
    # 正文内容
    text = f"### {title}\n\n" \
           f"> ⏰ **时间**: {current_time}\n\n" \
           f"> ⏱️ **耗时**: {duration:.2f} 秒\n\n" \
           f"---\n\n" \
           f"#### 📊 **备份统计**\n" \
           f"- ✅ **成功**: {success_count} 台\n" \
           f"- ❌ **失败**: {fail_count} 台\n\n"

    # 如果有失败设备，用红色高亮显示
    if failed_devices:
        text += f"---\n#### 🚫 **失败列表**:\n"
        for dev in failed_devices:
            text += f"- **{dev.get('hostname', '未知')}** ({dev['ip']})\n"
    
    # 添加点击跳转链接
    text += f"\n---\n" \
            f"🔗 [点击登录 Web 管理台查看详情]({web_url})\n"

    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text
        },
        "at": {
            "atMobiles": [],  # 不艾特任何人
            "isAtAll": False
        }
    }
    
    try:
        resp = requests.post(DINGTALK_WEBHOOK, json=data)
        logging.info(f"钉钉通知发送结果: {resp.text}")
    except Exception as e:
        logging.error(f"发送钉钉通知失败: {e}")

def backup_device(device):
    """备份单个设备配置"""
    ip = device['ip']
    username = device['username']
    password = device['password']
    hostname = device.get('hostname', ip)
    
    logging.info(f"开始备份设备: {hostname} ({ip})")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(ip, port=22, username=username, password=password, timeout=20, allow_agent=False, look_for_keys=False)
        chan = ssh.invoke_shell()
        time.sleep(1)
        
        # 华为命令
        chan.send("screen-length 0 temporary\n")
        time.sleep(1)
        chan.send("display saved-configuration\n")
        time.sleep(3)
        
        output = ""
        while True:
            if chan.recv_ready():
                chunk = chan.recv(8192).decode('utf-8', errors='ignore')
                output += chunk
                if "return" in chunk and ">" in chunk: 
                    break
            else:
                time.sleep(1)
                if len(output) > 0 and time.time() % 10 == 0: break
        
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            
        # 强制使用北京时间生成文件名
        timestamp = datetime.datetime.now(BJ_TZ).strftime("%Y%m%d_%H%M%S")
        filename = f"{hostname}_{timestamp}.cfg"
        filepath = os.path.join(BACKUP_DIR, filename)
        
        save_content = output.replace("display saved-configuration", "", 1).strip()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(save_content)
            
        logging.info(f"备份成功: {filename}")
        ssh.close()
        return True, device
        
    except Exception as e:
        logging.error(f"备份失败 {hostname} ({ip}): {e}")
        if ssh: ssh.close()
        return False, device

def cleanup_old_backups():
    """清理过期备份"""
    # 略去清理逻辑，保持原样即可
    pass 

def main():
    start_time = time.time()
    config = load_devices()
    devices = config.get('devices', [])
    
    if not devices:
        logging.error("没有找到设备信息")
        return

    success_count = 0
    fail_count = 0
    failed_devices = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(backup_device, dev) for dev in devices]
        for future in futures:
            success, dev = future.result()
            if success:
                success_count += 1
            else:
                fail_count += 1
                failed_devices.append(dev)

    # 计算总耗时
    total_duration = time.time() - start_time
    
    # 发送通知 (传入耗时)
    send_dingtalk_alert(success_count, fail_count, failed_devices, total_duration)
    
    logging.info(f"所有任务完成，耗时: {total_duration:.2f}秒")

if __name__ == "__main__":
    main()
