import pandas as pd, numpy as np, json, glob
B='veri_abd/'
m=json.load(open(B+'cikti/abd_metrics.json',encoding='utf8'))
fl=json.load(open(B+'belgelenmis_yanginlar_abd.json',encoding='utf8'))['yanginlar']
ev=pd.read_parquet(B+'cikti/abd_events.parquet').set_index('event_id')
df=pd.concat([pd.read_parquet(f,columns=['acq_datetime_utc','latitude','longitude','sensor','type']) for f in sorted(glob.glob(B+'parquet/*.parquet'))])
df=df[df['type']==0].copy(); df['t']=pd.to_datetime(df.acq_datetime_utc,utc=True)
lat=np.radians(df.latitude.values); lon=np.radians(df.longitude.values)
pl={r['ad']:r for r in m['dogrulama']['liste']}
rows=[]
def hav(la1,lo1,la2,lo2):
    la1,lo1,la2,lo2=map(np.radians,(la1,lo1,la2,lo2))
    a=np.sin((la2-la1)/2)**2+np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2
    return 2*6371.0088*np.arcsin(np.sqrt(a))
for f in fl:
    s=pd.Timestamp(f['baslangic'],tz='UTC'); a=s-pd.Timedelta(days=3); b=s+pd.Timedelta(days=30)
    sel=df[(df.t>=a)&(df.t<=b)]
    d=hav(f['lat'],f['lon'],sel.latitude.values,sel.longitude.values)
    w=sel[d<=40]; 
    p=pl[f['ad']]; r=dict(ad=f['ad'],yil=s.year,raw40=len(w),raw_modis=int((w.sensor=='MODIS').sum()),raw_viirs=int((w.sensor=='VIIRS').sum()),durum=p['durum'])
    if p['durum']=='eslesti':
        e=ev.loc[p['event_id']]
        r.update(ev_tespit=p['tespit'],ev_n=int(e.n),ev_dist_ben=round(float(hav(f['lat'],f['lon'],e.lat,e.lon)),1),ev_dist_pipe=p['uzaklik_km'],ev_t0=str(e.t0)[:16],ev_sure=p['sure_sa'],oran=round(p['tespit']/max(len(w),1),3),yil_sirasi=p['yil_sirasi'])
    else:
        # en yakin buyuk kume? sadece ham sayim
        pass
    rows.append(r)
R=pd.DataFrame(rows); pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
print(R.to_string()); R.to_csv(B+'cikti/bagimsiz_kontrol/yangin_sonuc.csv',index=False)
