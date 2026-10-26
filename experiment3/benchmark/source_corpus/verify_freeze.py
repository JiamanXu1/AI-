#!/usr/bin/env python3
"""Verify a frozen corpus without network calls or content changes."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
m=json.loads((root/'freeze_manifest.json').read_text())
errors=[]
for name,expected in m['files'].items():
    p=root/name
    if not p.is_file():errors.append({'file':name,'problem':'missing'});continue
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if actual!=expected:errors.append({'file':name,'problem':'sha256_mismatch'})
print(json.dumps({'status':'PASS' if not errors else 'FAIL','files_checked':len(m['files']),'errors':errors},ensure_ascii=False,indent=2))
sys.exit(bool(errors))
