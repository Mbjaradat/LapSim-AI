"""Analytical sampling of the existing Ry(yaw) Rx(pitch) rigid shaft model.

This characterizes reach, not collisions or anatomical/biomechanical accuracy.
The contact point is the closed-jaw midline, offset beyond the shaft reference.
"""
from math import asin, atan2, cos, degrees, radians, sin, sqrt
from lapsim_ai.control.instrument import InstrumentControl


def contact_point(pivot, pose, jaw_offset):
    yaw, pitch = radians(pose.yaw), radians(pose.pitch)
    radius = pose.insertion + jaw_offset
    axis = (-sin(yaw)*cos(pitch), sin(pitch), -cos(yaw)*cos(pitch))
    return tuple(p + radius*a for p,a in zip(pivot,axis))


def inverse_contact(pivot, point, jaw_offset):
    x,y,z = (v-p for v,p in zip(point,pivot))
    radius = sqrt(x*x+y*y+z*z)
    if radius <= jaw_offset or z >= 0:
        return None
    return InstrumentControl(degrees(atan2(-x,-z)), degrees(asin(y/radius)), radius-jaw_offset, 0, 0)


def reachable(pivot, point, limits, jaw_offset, margin=0):
    pose = inverse_contact(pivot,point,jaw_offset)
    if pose is None:
        return False
    return all(low+(high-low)*margin <= getattr(pose,name) <= high-(high-low)*margin
               for name in ('yaw','pitch','insertion') for low,high in (getattr(limits,name),))


def sample_workspace(pivot, limits, jaw_offset, steps=11):
    if steps < 2:
        raise ValueError('At least two samples per axis required')
    def axis(name):
        low,high=getattr(limits,name)
        return [low+(high-low)*i/(steps-1) for i in range(steps)]
    return [contact_point(pivot,InstrumentControl(y,p,d),jaw_offset)
            for y in axis('yaw') for p in axis('pitch') for d in axis('insertion')]


def bounds(points):
    return tuple((min(p[i] for p in points),max(p[i] for p in points)) for i in range(3))


def characterize(pivots, neutral, limits, jaw_offset, steps=11, spacing=.01, margin=.10):
    clouds={side:sample_workspace(p,limits,jaw_offset,steps) for side,p in pivots.items()}
    boxes={side:bounds(points) for side,points in clouds.items()}
    # Bounding-box intersection only seeds a grid; inverse kinematics confirms
    # every shared point. AABB membership alone is not evidence of reachability.
    lo=[max(box[i][0] for box in boxes.values()) for i in range(3)]
    hi=[min(box[i][1] for box in boxes.values()) for i in range(3)]
    axes=[[lo[i]+j*spacing for j in range(max(0,int((hi[i]-lo[i])/spacing)+1))] for i in range(3)]
    shared=[(x,y,z) for x in axes[0] for y in axes[1] for z in axes[2]
            if all(reachable(p,(x,y,z),limits,jaw_offset,margin) for p in pivots.values())]
    neutral_tips=[contact_point(p,neutral[side],jaw_offset) for side,p in pivots.items()]
    center=tuple(sum(p[i] for p in neutral_tips)/len(neutral_tips) for i in range(3))
    if not shared or not all(reachable(p,center,limits,jaw_offset,margin) for p in pivots.values()):
        raise ValueError('No comfortable shared neutral-centered workspace; inspect geometry before building')
    return dict(clouds=clouds,bounds=boxes,shared=shared,center=center,
                margin=margin,spacing=spacing,steps=steps)
