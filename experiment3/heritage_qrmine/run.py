"""Reproduce the frozen analysis; no network required after dependency installation."""
from pathlib import Path
import argparse,subprocess,sys,os
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true',help='Attempt missing source downloads before analysis; may change corpus/results');p.add_argument('--offline',action='store_true',help='Explicit default: use frozen source snapshots');p.add_argument('--verify-only',action='store_true');a=p.parse_args()
if a.fetch and a.offline:p.error('--fetch and --offline are mutually exclusive')
env=os.environ.copy();env.setdefault('MPLCONFIGDIR','/tmp/heritage-mpl');env.setdefault('PYTHONHASHSEED','42');env.setdefault('OMP_NUM_THREADS','1')
stages=['verify'] if a.verify_only else (['fetch'] if a.fetch else [])+['extract','mine','analyze','interpret','bilingual','report','verify']
for stage in stages:
 print('Running',stage,flush=True);subprocess.run([sys.executable,str(R/'scripts'/f'{stage}.py')],cwd=R,env=env,check=True)
