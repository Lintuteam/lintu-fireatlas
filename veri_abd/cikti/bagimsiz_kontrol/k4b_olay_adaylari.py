import pandas as pd, numpy as np, json
B='veri_abd/'
fl={f['ad']:f for f in json.load(open(B+'belgelenmis_yanginlar_abd.json',encoding='utf8'))['yanginlar']}
m={r['ad']:r for r in json.load(open(B+'cikti/abd_metrics.json',encoding='utf8'))['dogrulama']['liste']}
ev=pd.read_parquet(B+'cikti/abd_events.parquet')
def hav(la1,lo1,la2,lo2):
    la1,lo1,la2,lo2=map(np.radians,(la1,lo1,la2,lo2))
    a=np.sin((la2-la1)/2)**2+np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2
    return 2*6371.0088*np.arcsin(np.sqrt(a))
for ad in ['Rock House Fire','Las Conchas Fire','Valley Fire','Pains Bay Fire','Pagami Creek Fire','Whitewater-Baldy Complex Fire','Honey Prairie Fire','Schultz Fire','Ash Creek Fire','Wood Hollow Fire','Rough Fire']:
    f=fl[ad]; s=pd.Timestamp(f['baslangic'],tz='UTC')
    d=hav(f['lat'],f['lon'],ev.lat.values,ev.lon.values)
    w=ev[(d<=40)&(ev.t0>=s-pd.Timedelta(days=3))&(ev.t0<=s+pd.Timedelta(days=30))].copy()
    w['km']=d[(d<=40)&(ev.t0>=s-pd.Timedelta(days=3))&(ev.t0<=s+pd.Timedelta(days=30))]
    print('==',ad,f['baslangic'],'n_events_in_window',len(w),'sum n',w.n.sum(),'matched',m[ad].get('event_id'),m[ad].get('tespit'))
    print(w.sort_values('n',ascending=False).head(4)[['event_id','n','n_modis','n_viirs','sure_sa','t0','km']].to_string())
