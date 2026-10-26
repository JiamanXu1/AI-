"""Two complete frozen runs, comparing content-derived outputs byte for byte."""
from pathlib import Path
import subprocess,sys,hashlib,json,os
R=Path(__file__).resolve().parents[1]
names=['data/units.jsonl','results/qrmine_terms.csv','results/qrmine_categories_and_dictionary.txt','results/supplemental_nmf_topics.csv','results/supplemental_nmf_assignments.csv','results/category_coverage.csv','results/interpretive_coding.csv','results/bilingual_pair_summary.csv','results/bilingual_reviewed_presence.csv','results/stats.json','results/扎根分析结果.md','results/扎根分析结果.html']
def hashes():return {n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in names}
def main():
 outcomes=[]
 for n in [1,2]:
  with (R/'results'/f'offline_run_{n}.log').open('w') as log:
   subprocess.run([sys.executable,str(R/'run.py'),'--offline'],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
  outcomes.append(hashes());print('Offline run',n,'finished',flush=True)
 unequal=[n for n in names if outcomes[0][n]!=outcomes[1][n]]
 report=dict(status='passed' if not unequal else 'failed',runs=2,files_compared=len(names),differences=unequal,hashes=outcomes[1],scope='same frozen inputs and installed environment; no claim of cross-platform bitwise identity')
 (R/'results/reproducibility_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 assert not unequal,unequal
if __name__=='__main__':main()
