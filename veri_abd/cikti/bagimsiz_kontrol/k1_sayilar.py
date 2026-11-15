import pandas as pd, numpy as np, json, glob
B='veri_abd/'
cols=['acq_datetime_utc','latitude','longitude','sensor','satellite','frp_mw','scan_km','track_km','daynight','type','confidence_cls']
df=pd.concat([pd.read_parquet(f,columns=cols) for f in sorted(glob.glob(B+'parquet/firms_abd_*.parquet'))],ignore_index=True)
m=json.load(open(B+'cikti/abd_metrics.json',encoding='utf8'))
out={}
out['rows_all']=len(df); out['rows_lon']=int((df.longitude<=-60).sum())
out['type_counts']=df['type'].value_counts().to_dict()
df['ts']=pd.to_datetime(df.acq_datetime_utc,utc=True)
df['yil']=df.ts.dt.year
print(out)
a=df[df.longitude<=-60]
c=a[a['type']==0]
ys=a.groupby(['yil','sensor']).size().unstack(fill_value=0)
print('yil_sensor all types\n',ys)
yc=c.groupby(['yil','sensor']).size().unstack(fill_value=0); print('clean\n',yc)
mod=yc['MODIS'].astype(float); vi=yc['VIIRS'].astype(float); ham=mod+vi
J=lambda s:(s.loc[2012:2014].mean()-s.loc[2009:2011].mean())/s.loc[2009:2011].mean()*100
print('jump ham',J(ham),'modis',J(mod))
yrs=[2012,2013,2014,2015]
pred={};err={}
for y in yrs:
    o=[z for z in yrs if z!=y]; r=mod[o].sum()/vi[o].sum(); pred[y]=r*vi[y]; err[y]=(pred[y]-mod[y])/mod[y]*100
print(pred,err,'mape',np.mean(np.abs(list(err.values()))))
es=mod.copy()
for y in yrs: es[y]=pred[y]
print(es.to_dict(),'jump esdeger',J(es))
# pipeline compare
print('pipe yillik',{k:(v['modis'],v['viirs']) for k,v in m['yillik'].items()})
print('pipe sicrama',m['sicrama'])
# sanity
print('dupes full-row', int(df.duplicated(['acq_datetime_utc','latitude','longitude','sensor','satellite']).sum()))
print('dupes incl type/frp', int(df.duplicated(['acq_datetime_utc','latitude','longitude','sensor','satellite','frp_mw']).sum()))
print('lat range',df.latitude.min(),df.latitude.max(),'lon',df.longitude.min(),df.longitude.max())
print('lat nan',df.latitude.isna().sum(),df.longitude.isna().sum(),'ts nan',df.ts.isna().sum())
print('ts range',df.ts.min(),df.ts.max(),'outside 2009-2015',int(((df.yil<2009)|(df.yil>2015)).sum()))
print('frp<=0',int((df.frp_mw<=0).sum()),'frp nan',int(df.frp_mw.isna().sum()),'frp max',df.frp_mw.max())
print(pd.crosstab(df.sensor,df.satellite))
print(pd.crosstab(df.sensor,df.yil))
print('daynight',df.daynight.value_counts().to_dict())
print('conf',pd.crosstab(df.sensor,df.confidence_cls))
print('scan/track',df.groupby('sensor')[['scan_km','track_km']].describe().T)
print('lon>-60',int((df.longitude>-60).sum()),'lon>0',int((df.longitude>0).sum()))
print('sat by year',pd.crosstab(df.satellite,df.yil))
print('VIIRS 2012 first date',df[df.sensor=='VIIRS'].ts.min())
print('type by sensor',pd.crosstab(df.sensor,df['type']))
# ts vs source year file
