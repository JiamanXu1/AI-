"""Actual QRMine 4.0.0 exploratory NLP. Never equate machine terms with GT categories."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/heritage-qrmine-mpl')
os.environ.setdefault('OMP_NUM_THREADS','1')
from pathlib import Path
import json,random,contextlib,io,csv,platform,importlib.metadata
import numpy as np
from qrmine import Content,Qrmine,ReadData
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
R=Path(__file__).resolve().parents[1]
def writecsv(path,rows):
 if rows:
  with path.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 random.seed(42);np.random.seed(42)
 sources=json.loads((R/'config/sources.json').read_text());included={q['id'] for q in json.loads((R/'results/extraction_audit.json').read_text()) if q['status']=='included'}
 docs=[d for d in sources if d['id'] in included and d['lang']=='en' and d['kind']!='paired_only']
 texts=[(R/'data/text'/f"{d['id']}.txt").read_text() for d in docs]
 combined='\n\n'.join(t+'\n<break>'+d['id']+'</break>' for d,t in zip(docs,texts))+'\n'
 (R/'data/qrmine_en.txt').write_text(combined)
 reader=ReadData();reader.read_file(str(R/'data/qrmine_en.txt'));assert len(reader.documents)==len(docs)
 q=Qrmine();rows=[];logs=[]
 for d,t in zip(docs,texts):
  print('QRMine',d['id'],flush=True);c=Content(t,title=d['id'])
  buffer=io.StringIO()
  with contextlib.redirect_stdout(buffer):
   q.print_categories(c.doc,num=30);q.print_dict(c,num=20,top_n=3)
  logs.append('\n=== '+d['id']+' ===\n'+buffer.getvalue())
  for pos,words in [('noun',c.common_nouns(40)),('verb',c.common_verbs(30))]:
   for term,count in words:rows.append(dict(doc_id=d['id'],pos=pos,term=term,count=count))
 writecsv(R/'results/qrmine_terms.csv',rows)
 (R/'results/qrmine_categories_and_dictionary.txt').write_text('\n'.join(logs))
 # Explicitly supplemental, NOT QRMine's default LDA: reproducible model and sensitivity k.
 vec=TfidfVectorizer(stop_words='english',min_df=2,max_df=.95,ngram_range=(1,2),sublinear_tf=True)
 x=vec.fit_transform(texts);terms=vec.get_feature_names_out();topic_rows=[];assign=[]
 for k in [4,6,8]:
  model=NMF(n_components=k,init='nndsvda',random_state=42,max_iter=1000);w=model.fit_transform(x)
  for j,h in enumerate(model.components_):topic_rows.append(dict(k=k,topic=j,terms=' | '.join(terms[h.argsort()[::-1][:15]])))
  for d,weights in zip(docs,w):
   z=weights.sum()
   for j,v in enumerate(weights):assign.append(dict(k=k,doc_id=d['id'],topic=j,weight=float(v/z) if z else 0))
 writecsv(R/'results/supplemental_nmf_topics.csv',topic_rows);writecsv(R/'results/supplemental_nmf_assignments.csv',assign)
 versions={p:importlib.metadata.version(p) for p in ['qrmine','spacy','en-core-web-sm','numpy','textacy','scikit-learn','pypdf']}
 (R/'results/runtime.json').write_text(json.dumps(dict(python=platform.python_version(),platform=platform.platform(),versions=versions,seed=42,qrmine_documents=len(docs),qrmine_methods=['ReadData.read_file','Content.common_nouns','Content.common_verbs','Qrmine.print_categories','Qrmine.print_dict'],supplement='TF-IDF+NMF via scikit-learn; k=4,6,8; not QRMine LDA'),indent=2))
 print('Finished',len(docs),'documents')
if __name__=='__main__':main()
