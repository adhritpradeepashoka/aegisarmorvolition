import numpy as np, trimesh, math
from manifold3d import Manifold, Mesh
from skel import *
def man(t): return Manifold(Mesh(vert_properties=np.array(t.vertices,dtype=np.float32),tri_verts=np.array(t.faces,dtype=np.uint32)))
def load(f): return man(trimesh.load(f))
def sph(r,c): return Manifold.sphere(r,20).translate([float(x) for x in c])
def tube(pts,radii):
    segs=[Manifold.batch_hull([sph(radii[i],pts[i]),sph(radii[i+1],pts[i+1])]) for i in range(len(pts)-1)]
    out=segs[0]
    for s in segs[1:]: out=out+s
    return out
ico=trimesh.creation.icosphere(1).vertices
def hull_offset(P,off):
    Q=(P[:,None,:]+off*ico[None,:,:]).reshape(-1,3); return man(trimesh.convex.convex_hull(Q))
H=to_exo(hum.vertices)
def centre_line(P,zs):
    out=[]
    for z in zs:
        s=P[(P[:,2]<z+15)&(P[:,2]>z-15)]; out.append([s[:,0].mean(),s[:,1].mean(),z])
    return np.array(out)
F0=to_exo(forearm_pts(0))
fore_zs=np.arange(-5,-251,-25.0); fore_c=centre_line(F0,fore_zs); fore_c[0]=[0,0,-5]
fore_r=[35.0 if z>=-100 else 35.0-(10.0*(-100-z)/150.0) for z in fore_zs]
up_zs=np.arange(40,291,25.0); up_c=centre_line(H,up_zs)
up_r=[(34.0+(4.2)*min(1,(z-40)/60.0)) for z in up_zs]
def forearm_env(q,pad=0.0):
    T=tube(fore_c,[r+pad for r in fore_r]); return T.rotate([q,0,0])
def upper_env(pad=0.0):
    t=tube(up_c,[r+pad for r in up_r])
    cond=hull_offset(H[H[:,2]<48],8.0+pad)      # distal humerus + 8 mm tissue
    return t+cond
