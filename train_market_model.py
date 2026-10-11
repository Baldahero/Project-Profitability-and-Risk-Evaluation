"""Train the market-risk model (probability that a construction tender receives at most two bids)
and provide a prediction function for the decision-support prototype.
Usage: put united_kingdom_fts_2021 … 2026.xlsx next to this file, run `python train_market_model.py`.
"""
import numpy as np, pandas as pd, joblib
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
NUM=['logval','val_missing','lots','buyer_n','gpa','dps','framework','eauction']
CAT=['procedure','legal','above','cpv3','buyer_type']
def btype(n):
    n=str(n).lower()
    for k,v in [('nhs','health'),('hospital','health'),('council','council'),('borough','council'),('county','council'),('university','education'),('college','education'),('school','education'),('academy','education'),('housing','housing'),('homes','housing'),('police','police'),('ministry','central'),('department','central'),('agency','central')]:
        if k in n: return v
    return 'other'
def features(df):
    def col(name, default):
        return df[name] if name in df else pd.Series(default, index=df.index)
    f=pd.DataFrame(index=df.index)
    v=pd.to_numeric(col('estimated_value',np.nan),errors='coerce')
    f['logval']=np.log10(v.where(v>0)); f['val_missing']=f.logval.isna().astype(int)
    f['lots']=pd.to_numeric(col('lots',1),errors='coerce').fillna(1).clip(upper=20)
    f['buyer_n']=pd.to_numeric(col('buyer_n',1),errors='coerce').fillna(1).clip(upper=50)
    for c in ['gpa','dps','framework','eauction']: f[c]=pd.to_numeric(col(c,0),errors='coerce').fillna(0).astype(int)
    f['procedure']=col('procedure','Unknown').astype(str); f['legal']=col('legal','Procurement Act 2023').astype(str); f['above']=col('above','nan').astype(str)
    f['cpv3']=col('cpv','NA').astype(str).str[:3]; f['buyer_type']=col('buyer_name','').map(btype)
    f['text']=col('title','').fillna('').astype(str)+' '+col('description','').fillna('').astype(str).str[:1500]
    return f
def build_dataset(years=(2021,2022,2023,2024,2025,2026)):
    M=[];B=[];L=[];I=[]
    for y in years:
        d=pd.read_excel(f'united_kingdom_fts_{y}.xlsx',sheet_name=['main','bids_statistics','tender_lots','tender_items'],engine='calamine')
        M.append(d['main']);B.append(d['bids_statistics']);L.append(d['tender_lots']);I.append(d['tender_items'])
    m=pd.concat(M).drop_duplicates('ocid',keep='last'); b=pd.concat(B); tl=pd.concat(L); ti=pd.concat(I)
    w=m[m.tender_mainProcurementCategory=='works'].copy()
    w['bids']=w.ocid.map(b[b.measure=='bids'].groupby('main_ocid').value.max())
    icpv=ti.dropna(subset=['classification_id']).groupby('main_ocid').classification_id.first()
    df=pd.DataFrame({'estimated_value':w.tender_value_amount,'lots':w.ocid.map(tl.drop_duplicates(['main_ocid','id']).groupby('main_ocid').size()).fillna(1),
        'buyer_n':w.groupby('buyer_name').ocid.transform('count'),'gpa':w.tender_coveredBy.notna().astype(int),
        'dps':w.tender_techniques_hasDynamicPurchasingSystem.fillna(False).astype(bool).astype(int),'framework':w.tender_techniques_hasFrameworkAgreement.fillna(False).astype(bool).astype(int),
        'eauction':w.tender_techniques_hasElectronicAuction.fillna(False).astype(bool).astype(int),'procedure':w.tender_procurementMethodDetails.fillna('Unknown'),
        'legal':np.where(w.tender_legalBasis_id.astype(str)=='2023/54','Procurement Act 2023','PCR 2015 / EU directives'),'above':w.tender_aboveThreshold.astype(str),
        'cpv':w.tender_classification_id.fillna(w.ocid.map(icpv)).astype(str),'buyer_name':w.buyer_name,'title':w.tender_title,'description':w.tender_description,'bids':w.bids})
    return df[df.bids.notna()&(df.bids<=200)]
def model():
    pre=ColumnTransformer([('n',Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler())]),NUM),('c',OneHotEncoder(handle_unknown='ignore',min_frequency=10),CAT),
        ('t',TfidfVectorizer(min_df=5,ngram_range=(1,2),max_features=20000,sublinear_tf=True,stop_words='english'),'text')])
    return Pipeline([('p',pre),('m',LogisticRegression(max_iter=3000,class_weight='balanced',C=1))])
def predict_tender_risk(tender: dict, path='market_risk_model.joblib', top=5):
    """tender: dict with keys estimated_value, procedure, title, description, cpv, buyer_name, lots, ... Returns probability and top contributing features."""
    mdl=joblib.load(path); X=features(pd.DataFrame([tender])); p=float(mdl.predict_proba(X)[0,1])
    z=mdl.named_steps['p'].transform(X); coef=mdl.named_steps['m'].coef_[0]; names=mdl.named_steps['p'].get_feature_names_out()
    contrib=np.asarray(z.multiply(coef).todense()).ravel() if hasattr(z,'multiply') else z.ravel()*coef
    idx=np.argsort(-np.abs(contrib))[:top]
    return {'p_low_competition':p,'top_factors':[(names[i],round(float(contrib[i]),3)) for i in idx]}
if __name__=='__main__':
    df=build_dataset(); y=(df.bids<=2).astype(int)
    mdl=model().fit(features(df),y); joblib.dump(mdl,'market_risk_model.joblib')
    print('trained on',len(df),'tenders; saved market_risk_model.joblib')
    print(predict_tender_risk({'estimated_value':450000,'procedure':'Open procedure','title':'Window and door replacement','description':'Replacement of windows and external doors at a primary school','cpv':'45421100','buyer_name':'Example Borough Council'}))
