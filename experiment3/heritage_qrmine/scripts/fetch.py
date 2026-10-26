"""Download only manifest URLs; freeze raw bytes and log failures, no silent replacements."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import requests,json,hashlib,time,argparse,subprocess,tempfile
R=Path(__file__).resolve().parents[1]
def fetch(d):
 out=R/'data/raw'/d['id']; meta=out.with_suffix('.json')
 if meta.exists():
  m=json.loads(meta.read_text())
  if m.get('status')=='ok':return m
 m=dict(d, retrieved_at=datetime.now(timezone.utc).isoformat())
 for attempt in range(3):
  try:
   tmp=out.with_suffix('.download')
   proc=subprocess.run(['curl','-f','-L','--silent','--show-error','--max-time','60','-o',str(tmp),'-w','%{url_effective}',d['url']],capture_output=True,text=True)
   if proc.returncode:raise RuntimeError(proc.stderr.strip())
   b=tmp.read_bytes();tmp.unlink()
   if len(b)<200:raise ValueError('Response too short')
   ext='.pdf' if b.startswith(b'%PDF') else '.html'
   path=out.with_suffix(ext);path.write_bytes(b)
   m.update(status='ok',final_url=proc.stdout,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),raw_path=str(path.relative_to(R)),content_type=('application/pdf' if ext=='.pdf' else 'text/html'))
   break
  except Exception as e:m.update(status='error',error=str(e));time.sleep(1)
 meta.write_text(json.dumps(m,ensure_ascii=False,indent=2));print(d['id'],m['status'],flush=True);return m
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ids',nargs='*');args=p.parse_args();docs=json.loads((R/'config/sources.json').read_text());docs=[d for d in docs if not args.ids or d['id'] in args.ids]
 with ThreadPoolExecutor(max_workers=4) as pool:logs=list(pool.map(fetch,docs))
 (R/'results/fetch_log.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2))
