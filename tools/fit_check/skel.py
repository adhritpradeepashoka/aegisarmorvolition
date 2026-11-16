import numpy as np, trimesh
from vtp import read_vtp
G="/tmp/osm/Geometry/"
J=np.array([0.0061,-0.2904,-0.0123]); A=np.array([0.0494,0.0366,0.99810825]); A/=np.linalg.norm(A)
PERM=np.array([[0,0,1],[1,0,0],[0,1,0]],float)   # os (x ant,y up,z right) -> exo (X right, Y ant, Z up)
def rot(axis,ang):
    return trimesh.transformations.rotation_matrix(ang,axis)[:3,:3]
def align_to_x():   # rotate so joint axis (in exo frame) is exactly +X
    a=PERM@A; v=np.cross(a,[1,0,0]); s=np.linalg.norm(v); c=a@np.array([1,0,0])
    return trimesh.transformations.rotation_matrix(np.arctan2(s,c),v/s)[:3,:3] if s>1e-9 else np.eye(3)
RA=align_to_x()
def to_exo(p_os_hum):          # points in humerus frame (m) -> exo frame (mm), elbow centre at origin, axis = +X
    return ((RA@(PERM@(np.asarray(p_os_hum)-J).T)).T)*1000.0
hum=read_vtp(G+"arm_r_humerus.vtp"); uln=read_vtp(G+"arm_r_ulna.vtp"); rad=read_vtp(G+"arm_r_radius.vtp")
def forearm_pts(q_deg):        # ulna+radius vertices (child frame == parent frame at q=0) -> humerus frame
    R=rot(A,np.radians(q_deg)); P=np.vstack([uln.vertices,rad.vertices])
    return J+ (R@P.T).T
