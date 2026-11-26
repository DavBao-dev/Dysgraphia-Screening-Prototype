import sys,zipfile,io,re,json,numpy as np,pandas as pd,tempfile,os
sys.path.insert(0,sys.argv[1]); from feat import features
from sklearn.metrics import roc_auc_score
from scipy.stats import mannwhitneyu
z=zipfile.ZipFile(sys.argv[1]+'/diagramo/DiaGraMo-project.zip'); n=z.namelist()
c=pd.read_csv(io.BytesIO(z.read('DiaGraMo-project/data/processed_data/cognitive_test_data/cognitiveTestCSV2data_cleaned.csv')),sep=';',decimal=',',engine='python',on_bad_lines='skip')
lab=dict(zip(c.id_participant,c.group))
def load(b):
    L=[l.split() for l in b.decode('utf8','ignore').strip().splitlines()[1:]]
    L=[r[:7] for r in L if len(r)>=4]
    return np.array(L,dtype=float) if len(L)>50 else None
rows=[]
tasks={'copy':r'TSK1[56]\(TA\)-copy','loops':r'TSK9\(TA\)-lower-loops-fast'}
for f in n:
    if not f.endswith('_1.svc'): continue
    cid=f.split('/')[-2]
    if cid not in lab or pd.isna(lab[cid]): continue
    for tk,pat in tasks.items():
        if re.search(pat,f):
            a=load(z.read(f))
            if a is None: continue
            for hz,nm in [(None,'native'),(30,'30Hz')]:
                o=features(a,hz)
                if o: rows.append(dict(id=cid,y=int(lab[cid]),task=tk,rate=nm,**o))
df=pd.DataFrame(rows); df.to_csv(sys.argv[1]+'/dg_features.csv',index=False)
rng=np.random.default_rng(0)
feats=[k for k in df.columns if k not in('id','y','task','rate')]
out=[]
for (tk,rt),g in df.groupby(['task','rate']):
    for ft in feats:
        d=g[['y',ft]].dropna()
        if d.y.nunique()<2: continue
        auc=roc_auc_score(d.y,d[ft]); bs=[]
        for _ in range(1000):
            i=rng.integers(0,len(d),len(d)); s=d.iloc[i]
            if s.y.nunique()==2: bs.append(roc_auc_score(s.y,s[ft]))
        p=mannwhitneyu(d[d.y==1][ft],d[d.y==0][ft]).pvalue
        out.append(dict(task=tk,rate=rt,feature=ft,n1=int((d.y==1).sum()),n0=int((d.y==0).sum()),AUC=round(auc,3),lo=round(np.percentile(bs,2.5),3),hi=round(np.percentile(bs,97.5),3),p=p))
r=pd.DataFrame(out); r.to_csv(sys.argv[1]+'/dg_auc.csv',index=False)
pd.set_option('display.width',200); print(r.to_string())
