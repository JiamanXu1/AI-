#!/usr/bin/env python3
"""无密钥网络诊断：不调用模型，不输出代理地址或凭据。"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
env = {k: v for k, v in os.environ.items() if not k.endswith('_API_KEY')}
proxy_keys = ('https_proxy', 'HTTPS_PROXY', 'http_proxy', 'HTTP_PROXY', 'all_proxy', 'ALL_PROXY', 'no_proxy', 'NO_PROXY')
report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
          'proxy_environment_present': {k: bool(env.get(k)) for k in proxy_keys},
          'api_key_used': False, 'checks': []}
curl_executable = '/usr/bin/curl' if sys.platform == 'darwin' and Path('/usr/bin/curl').exists() else 'curl'
report['curl_executable'] = curl_executable
for url in ('https://console.mistral.ai/', 'https://api.mistral.ai/v1/models'):
    host = url.split('/')[2]
    check = {'url': url}
    try:
        socket.getaddrinfo(host, 443)
        check['dns_resolved'] = True
    except OSError:
        check['dns_resolved'] = False
    print('正在检查：', host, flush=True)
    try:
        result = subprocess.run([curl_executable, '--disable', '--http1.1', '--silent', '--show-error',
            '--connect-timeout', '15', '--max-time', '20', '--output', os.devnull,
            '--write-out', '%{http_code} %{http_connect}', url], capture_output=True, text=True, timeout=25, env=env)
        statuses = result.stdout.strip().split()
        check.update(curl_exit_code=result.returncode,
                     http_status=statuses[0] if statuses else '000',
                     proxy_connect_http_status=statuses[1] if len(statuses) > 1 else '000')
        error = result.stderr.strip()
        for k in proxy_keys:
            if env.get(k):
                error = error.replace(env[k], '[PROXY_REDACTED]')
        check['error'] = error
    except (OSError, subprocess.TimeoutExpired) as exc:
        check['error'] = type(exc).__name__
    report['checks'].append(check)
    print(json.dumps(check, ensure_ascii=False), flush=True)
    (ROOT / 'mistral_connection_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print('诊断已保存：', ROOT / 'mistral_connection_check.json')
print('API返回401/403等HTTP状态表示已连到HTTP服务；000伴随超时表示尚未获得HTTP响应。')
