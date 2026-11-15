import sys; sys.path.insert(0,'veri_abd/cikti/bagimsiz_kontrol')
from k3_kume import *
for y in (2009,2013):
    s,x,yy,t=load(y)
    for r,dt in [(1,72),(1,24),(1,12),(0.7,72),(1.5,72)]:
        kj,_=ncomp(x,yy,t,r,dt*3600); ks=0
        for msk in (s=='MODIS',s=='VIIRS'):
            ks+=ncomp(x[msk],yy[msk],t[msk],r,dt*3600)[0]
        print(y,r,dt,'joint',kj,'sep',ks,'share%.1f'%((ks-kj)/kj*100))
