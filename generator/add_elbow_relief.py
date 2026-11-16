#!/usr/bin/env python3
"""
Cut an elbow relief into the upper cuff so the (modelled) human forearm can swing past it.
Human forearm is modelled as a plain cylinder (r = FOREARM_CIRC/2pi) hinged on the elbow axis (X through
the origin), swept from -5 to 95 degrees flexion, plus a margin for skin/padding. This is a crude model: measure a real arm.

usage: python3 add_elbow_relief.py <in.stl> <out.stl> [margin_mm=6] [scale=1.0]
(scale=0.4 for the mini set)
"""
import os, sys, math, numpy as np, trimesh
from manifold3d import Manifold, Mesh
FOREARM_CIRC=220.0
SEG=int(os.environ.get('SEG','100'))
src,dst=sys.argv[1],sys.argv[2]
margin=float(sys.argv[3]) if len(sys.argv)>3 else 6.0
scale=float(sys.argv[4]) if len(sys.argv)>4 else 1.0
t=trimesh.load(src)
m=Manifold(Mesh(vert_properties=np.array(t.vertices,dtype=np.float32),tri_verts=np.array(t.faces,dtype=np.uint32)))
rf=(FOREARM_CIRC/(2*math.pi)+margin)*scale
def cyl(r,z0,z1): return Manifold.cylinder(z1-z0,r,r,SEG,False).translate([0,0,z0])
env=None
for d in np.arange(-5,95.1,2.5):
    c=cyl(rf,-250*scale,0.0137).rotate([float(d),0,0])
    env=c if env is None else env+c
out=m-env
me=out.to_mesh()
o=trimesh.Trimesh(np.asarray(me.vert_properties)[:,:3],np.asarray(me.tri_verts),process=True)
parts=o.split(only_watertight=False)
o=max(parts,key=lambda p:len(p.faces))   # drop the zero-area sliver faces the boolean leaves behind
o.export(dst)
print(f"removed {m.volume()-out.volume():.0f} mm3 ({100*(m.volume()-out.volume())/m.volume():.1f}%), watertight={o.is_watertight}, dropped {len(parts)-1} degenerate sliver parts")
