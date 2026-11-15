import pandas as pd, glob
df=pd.concat([pd.read_parquet(f,columns=['sensor','type','frp_mw','confidence_cls','acq_datetime_utc']) for f in sorted(glob.glob('veri_abd/parquet/firms_abd_*.parquet'))])
z=df[df.frp_mw<=0]
print(len(z)); print(pd.crosstab(z.sensor,z['type'])); print(z.frp_mw.value_counts().head()); print(z.confidence_cls.value_counts())
print(((df.frp_mw<=0)&(df['type']==0)).sum(), 'clean frp<=0; share of clean', ((df.frp_mw<=0)&(df['type']==0)).sum()/(df['type']==0).sum())
print(df[df['type']==0].groupby('sensor').frp_mw.describe())
