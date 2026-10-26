"""Package research files, never the virtualenv or unrelated workspace files."""
from pathlib import Path
import zipfile,hashlib,json
R=Path(__file__).resolve().parents[1]
def main():
 def keep(p):return p.is_file() and not any(part in {'.venv','__pycache__','.git'} for part in p.relative_to(R).parts) and p.name not in {'.DS_Store','file_manifest.json'} and p.suffix!='.download'
 files=sorted(p for p in R.rglob('*') if keep(p))
 records={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 manifest=R/'file_manifest.json';manifest.write_text(json.dumps(records,ensure_ascii=False,indent=2));files.append(manifest)
 out=R.parent/'outputs'/'heritage_qrmine_2026-10-13.zip';out.parent.mkdir(exist_ok=True)
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:z.write(p,'heritage_qrmine/'+str(p.relative_to(R)))
 with zipfile.ZipFile(out) as z:assert z.testzip() is None
 print(json.dumps(dict(zip=str(out),files=len(files),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest()),ensure_ascii=False))
if __name__=='__main__':main()
