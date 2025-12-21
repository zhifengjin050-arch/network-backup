from flask import Flask, send_file, render_template_string, url_for, request
import os
import logging
from datetime import datetime
import json

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/app/backups")
logger.debug(f"BACKUP_DIR environment variable: {os.environ.get('BACKUP_DIR')}")
logger.debug(f"Using backup directory: {BACKUP_DIR}")

# 确保备份目录存在
if not os.path.exists(BACKUP_DIR):
	logger.debug(f"Backup directory does not exist, creating: {BACKUP_DIR}")
	os.makedirs(BACKUP_DIR, exist_ok=True)
else:
	logger.debug(f"Backup directory exists: {BACKUP_DIR}")

# 加载设备信息
with open("devices.json", "r") as f:
	devices = json.load(f)["devices"]

# HTML 模板（美化样式 + 空状态 + 响应式）
INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>Network Device Backups</title>
	<style>
		:root { --bg:#f8fafc; --card:#ffffff; --text:#0f172a; --muted:#64748b; --border:#e2e8f0; --brand:#2563eb; --brand-weak:#dbeafe; }
		html,body { height:100%; }
		body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji'; margin:0; background:var(--bg); color:var(--text); }
		.container { max-width: 1080px; margin: 0 auto; padding: 24px; }
		header { display:flex; align-items:center; justify-content:space-between; margin-bottom: 16px; }
		header h1 { font-size: 24px; margin: 0; }
		.meta { color: var(--muted); font-size: 14px; }
		.card { background: var(--card); border:1px solid var(--border); border-radius: 12px; padding: 16px; box-shadow: 0 8px 24px rgba(15,23,42,0.04); }
		.table-wrapper { overflow-x:auto; }
		table { border-collapse: collapse; width: 100%; min-width: 720px; }
		th, td { border-bottom: 1px solid var(--border); padding: 12px 10px; text-align: left; }
		th { background-color: #f9fafb; font-weight: 600; font-size: 14px; color: #334155; }
		tr:hover td { background-color: #fafafa; }
		.badge { display:inline-block; padding: 4px 8px; border-radius: 999px; background: var(--brand-weak); color: var(--brand); font-size: 12px; font-weight: 600; }
		.btn { display:inline-flex; align-items:center; gap:8px; padding: 8px 12px; border-radius: 8px; border:1px solid var(--border); background:#fff; color: var(--brand); text-decoration:none; font-weight:600; transition: all .15s ease; }
		.btn:hover { border-color: var(--brand); box-shadow: 0 4px 12px rgba(37,99,235,0.15); }
		.empty { text-align:center; padding: 36px 12px; color: var(--muted); }
		footer { text-align:center; color: var(--muted); font-size: 12px; margin-top: 16px; }
		.filter-form { display:flex; gap:10px; margin-bottom: 16px; }
		.filter-form input { padding: 8px; border: 1px solid var(--border); border-radius: 4px; }
		.filter-form button { padding: 8px 16px; background: var(--brand); color: white; border: none; border-radius: 4px; cursor: pointer; }
	</style>
</head>
<body>
	<div class="container">
		<header>
			<h1>Network Device Backups</h1>
			<div class="meta">共 <strong>{{ files|length }}</strong> 个备份，最后刷新：{{ now }}</div>
		</header>
		<div class="card">
			<form class="filter-form" method="get">
				<input type="text" name="device" placeholder="设备名" value="{{ request.args.get('device', '') }}">
				<input type="text" name="ip" placeholder="IP地址" value="{{ request.args.get('ip', '') }}">
				<button type="submit">筛选</button>
			</form>
			<div class="table-wrapper">
				<table>
					<tr>
						<th>文件名</th>
						<th>设备</th>
						<th>IP地址</th>
						<th>备份时间</th>
						<th>操作</th>
					</tr>
					{% if files and files|length > 0 %}
						{% for file in files %}
						<tr>
							<td><span class="badge">CFG</span> {{ file.filename }}</td>
							<td>{{ file.device }}</td>
							<td>{{ file.ip }}</td>
							<td>{{ file.time }}</td>
							<td><a class="btn" href="{{ url_for('download_file', filename=file.filename) }}">下载</a></td>
						</tr>
						{% endfor %}
					{% else %}
						<tr><td colspan="5" class="empty">暂无备份文件</td></tr>
					{% endif %}
				</table>
			</div>
		</div>
		<footer>备份目录：{{ backup_dir }}</footer>
	</div>
</body>
</html>
"""

@app.route('/')
def list_backups():
	logger.debug(f"Backup directory: {BACKUP_DIR}")
	logger.debug(f"Backup directory exists: {os.path.exists(BACKUP_DIR)}")
	files = []
	try:
		if os.path.exists(BACKUP_DIR):
			logger.debug(f"Contents of backup directory: {os.listdir(BACKUP_DIR)}")
			for filename in os.listdir(BACKUP_DIR):
				logger.debug(f"Processing file: {filename}")
				if filename.endswith(".cfg"):
					file_path = os.path.join(BACKUP_DIR, filename)
					logger.debug(f"File path: {file_path}")
					if os.path.exists(file_path):
						mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
						device = filename.split("_")[0]
						# 查找设备IP
						device_info = next((d for d in devices if d["hostname"].startswith(device)), None)
						ip = device_info["ip"] if device_info else "Unknown"
						files.append({"filename": filename, "device": device, "ip": ip, "time": mtime})
						logger.debug(f"Added file: {filename}")
					else:
						logger.debug(f"File does not exist: {file_path}")
				else:
					logger.debug(f"File does not match .cfg extension: {filename}")
			logger.debug(f"Total files found: {len(files)}")
		else:
			logger.debug("Backup directory does not exist")
			os.makedirs(BACKUP_DIR, exist_ok=True)
	except Exception as e:
		logger.error(f"Error reading backup directory: {str(e)}")
		files = []
	
	# 筛选功能
	device_filter = request.args.get("device", "").strip()
	ip_filter = request.args.get("ip", "").strip()
	
	if device_filter:
		files = [f for f in files if device_filter.lower() in f["device"].lower()]
	if ip_filter:
		files = [f for f in files if ip_filter in f["ip"]]
	
	files.sort(key=lambda x: x["time"], reverse=True)
	logger.debug(f"Files to display: {files}")
	return render_template_string(INDEX_HTML, files=files, now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), backup_dir=BACKUP_DIR)

@app.route('/download/<filename>')
def download_file(filename):
	file_path = os.path.join(BACKUP_DIR, filename)
	if os.path.exists(file_path):
		return send_file(file_path, as_attachment=True)
	return "File not found", 404

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000, debug=True)