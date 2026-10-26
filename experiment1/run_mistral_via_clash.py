#!/usr/bin/env python3
"""通过已核实的Clash Verge本机端口检查网络并采集Mistral问卷。"""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
# 2026-10-14从用户Clash Verge设置页面读取；订阅链接不是代理地址。
PROXY = 'http://127.0.0.1:7897'
env = os.environ.copy()
for name in ('http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY'):
    env[name] = PROXY
print('本次进程使用Clash代理：' + PROXY, flush=True)
print('请保持Clash Verge运行。先测试网络，不使用API密钥。', flush=True)
result = subprocess.run([sys.executable, str(ROOT / 'check_mistral_connection.py')], cwd=ROOT, env=env)
if result.returncode:
    sys.exit(result.returncode)
report = json.loads((ROOT / 'mistral_connection_check.json').read_text())
api = next(x for x in report['checks'] if x['url'] == 'https://api.mistral.ai/v1/models')
if api.get('curl_exit_code') != 0 or api.get('http_status') in ('', '000', None):
    print('代理网络检查尚未连通API，未采集问卷。诊断已保存，请让Codex检查。')
    sys.exit(2)
print('已收到API的HTTP响应；现在运行12题问卷。', flush=True)
sys.exit(subprocess.call([sys.executable, str(ROOT / 'run_experiment.py'),
    '--providers', 'mistral', '--prompt-key', '--transport', 'curl'], cwd=ROOT, env=env))
