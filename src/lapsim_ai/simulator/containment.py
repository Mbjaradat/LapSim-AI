"""Convex trainer bounds derived from board and camera geometry; no bpy."""
from math import sqrt


def trainer_planes(center,dimensions,floor,ceiling,camera,forward,right,up,tan_x,tan_y,inset=.04):
    """Planes encode inward unit normal dot point >= offset.

    Camera planes leave an inset on each image edge. The board footprint and
    explicit ceiling bound the physical work region; no visible walls are added.
    """
    planes=[]
    for axis,low,high,names in ((0,center[0]-dimensions[0]/2,center[0]+dimensions[0]/2,('left','right')),
                               (1,center[1]-dimensions[1]/2,center[1]+dimensions[1]/2,('front','back')),
                               (2,floor,ceiling,('floor','upper'))):
        n=[0.,0.,0.]; n[axis]=1.
        planes.append((names[0],tuple(n),low))
        planes.append((names[1],tuple(-v for v in n),-high))
    for label,axis,tangent in (('horizontal',right,tan_x),('vertical',up,tan_y)):
        for sign in (-1,1):
            n=tuple(f*tangent*(1-2*inset)+sign*a for f,a in zip(forward,axis))
            length=sqrt(sum(v*v for v in n)); n=tuple(v/length for v in n)
            planes.append((f'camera_{label}_{sign}',n,sum(a*b for a,b in zip(n,camera))))
    return tuple(planes)
