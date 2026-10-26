#!/usr/bin/env python3
"""Fetch metadata and response fingerprints; do not redistribute article HTML."""
import concurrent.futures, hashlib, json, re, subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
links=json.loads((ROOT/'data/link_register.json').read_text())
def check(row):
    result={'link_id':row['id'],'requested_url':row['url'],'checked_at_utc':datetime.now(timezone.utc).isoformat()}
    try:
        p=subprocess.run(['/usr/bin/curl','--disable','--location','--max-redirs','4','--connect-timeout','8','--max-time','20','--silent','--show-error','--write-out','\n%{http_code}\n%{url_effective}',row['url']],capture_output=True,timeout=24)
        result['curl_exit_code']=p.returncode
        if p.returncode:result['error']=p.stderr.decode(errors='replace')[:400];return result
        body,status,final=p.stdout.rsplit(b'\n',2)
        result.update(http_status=int(status),final_url=final.decode(),response_bytes=len(body),response_sha256=hashlib.sha256(body).hexdigest())
        head=body[:12000].decode('ascii',errors='ignore')
        charset=re.search(r'charset\s*=\s*["\x27]?([\w-]+)',head,re.I)
        encoding=charset.group(1) if charset else 'utf-8'
        if encoding.lower() in ('gb2312','gbk'):encoding='gb18030'
        try:text=body.decode(encoding,errors='replace')
        except LookupError:text=body.decode('utf-8',errors='replace')
        result['html_charset']=encoding
        title=re.search(r'<title[^>]*>(.*?)</title>',text,re.S|re.I)
        result['html_title']=re.sub(r'\s+',' ',title.group(1)).strip() if title else None
        result['palace_name_present']=any(k in text for k in ['古莱斯坦','古列斯坦','戈勒斯坦','玫瑰宫','古勒斯坦'])
        # Full body is used only transiently for a fingerprint, not saved or supplied as a transcription.
    except Exception as exc:result['error']=str(exc)[:400]
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(check,links))
(ROOT/'provenance/live_link_checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps({'checked':len(results),'http_200':sum(r.get('http_status')==200 for r in results),'with_palace_name':sum(r.get('palace_name_present',False) for r in results),'failed_ids':[r['link_id'] for r in results if r.get('http_status')!=200]},ensure_ascii=False))
