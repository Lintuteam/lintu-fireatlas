import pandas as pd, numpy as np, glob, sys, time
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
R=6371.0088
def ncomp(x,y,t,r=1.0,dt=72*3600):
    n=len(x)
    if n==0: return 0,0
    tree=cKDTree(np.c_[x,y]); tot=0; rows=[];cols=[]
    # chunked query to limit memory
    for s in range(0,n,200000):
        pr=tree.query_ball_point(np.c_[x[s:s+200000],y[s:s+200000]],r) if False else None
    pairs=tree.query_pairs(r,output_type='ndarray')
    npair=len(pairs)
    ok=np.abs(t[pairs[:,0]]-t[pairs[:,1]])<=dt
    pairs=pairs[ok]
    g=coo_matrix((np.ones(len(pairs),dtype=np.int8),(pairs[:,0],pairs[:,1])),shape=(n,n))
    k,_=connected_components(g,directed=False)
    return k,npair
def load(y):
    d=pd.read_parquet(f'veri_abd/parquet/firms_abd_{y}.parquet',columns=['acq_datetime_utc','latitude','longitude','sensor','type'])
    d=d[d['type']==0]
    t=pd.to_datetime(d.acq_datetime_utc,utc=True).astype('int64').to_numpy()//10**9
    lat=np.radians(d.latitude.to_numpy()); lon=np.radians(d.longitude.to_numpy())
    # equirectangular km; x uses per-point cos(lat)
    x=R*lon*np.cos(lat); yy=R*lat
    return d.sensor.to_numpy(),x,yy,t.astype(np.int64)
if __name__=='__main__':
    ev=pd.read_parquet('veri_abd/cikti/abd_events.parquet')
    res=[]
    for y in [int(a) for a in sys.argv[1:]]:
        t0=time.time()
        s,x,yy,t=load(y)
        kj,pj=ncomp(x,yy,t)
        km=s=='MODIS'; kv=s=='VIIRS'
        ks=0
        for msk in (km,kv):
            k,_=ncomp(x[msk],yy[msk],t[msk]); ks+=k
        pe=int((ev.yil==y).sum())
        r=dict(yil=y,n=len(s),n_modis=int(km.sum()),n_viirs=int(kv.sum()),joint=int(kj),separate=int(ks),dc_share=(ks-kj)/kj*100,pairs=pj,pipe_events_joint=pe,secs=round(time.time()-t0,1))
        print(r,flush=True); res.append(r)
    pd.DataFrame(res).to_csv('veri_abd/cikti/bagimsiz_kontrol/kume_sonuc_%s.csv'%'_'.join(sys.argv[1:]),index=False)
