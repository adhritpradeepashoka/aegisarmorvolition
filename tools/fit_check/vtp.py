import xml.etree.ElementTree as ET, numpy as np, trimesh
def read_vtp(path):
    r=ET.parse(path).getroot(); pd=r.find("PolyData/Piece")
    pts=np.array(pd.find("Points/DataArray").text.split(),dtype=float).reshape(-1,3)
    polys=pd.find("Polys"); d={a.get("Name"):np.array(a.text.split(),dtype=int) for a in polys.findall("DataArray")}
    con,off=d["connectivity"],d["offsets"]; faces=[]; s=0
    for e in off:
        f=con[s:e]; s=e
        for i in range(1,len(f)-1): faces.append([f[0],f[i],f[i+1]])
    return trimesh.Trimesh(pts,np.array(faces),process=True)
