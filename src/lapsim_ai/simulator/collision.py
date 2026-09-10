"""Deterministic joint-space constraints, without bpy, vision or mesh queries."""
from dataclasses import dataclass, replace
from math import sin, cos, radians, ceil, dist
from math import hypot


def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))


def segment_distance(p,q,a,b):
    """Closest distance between finite segments, including parallel/point cases."""
    u,v,w=sub(q,p),sub(b,a),sub(p,a)
    uu,vv,uv,uw,vw=dot(u,u),dot(v,v),dot(u,v),dot(u,w),dot(v,w)
    clamp=lambda x:min(1.,max(0.,x))
    if uu < 1e-15:
        s=0.; t=clamp(vw/vv) if vv>1e-15 else 0.
    else:
        if vv < 1e-15: t=0.; s=clamp(-uw/uu)
        else:
            denominator=uu*vv-uv*uv
            s=clamp((uv*vw-uw*vv)/denominator) if denominator>1e-15 else 0.
            t=(uv*s+vw)/vv
            if t<0: t=0.; s=clamp(-uw/uu)
            elif t>1: t=1.; s=clamp((uv-uw)/uu)
    return dist(add(p,mul(u,s)),add(a,mul(v,t)))


@dataclass(frozen=True)
class CollisionSettings:
    board_height: float = -.112
    shaft_radius: float = .003
    jaw_radius: float = .0025  # circumscribed 3 x 4 mm jaw cross-section
    jaw_length: float = .018
    hinge_offset: float = .0015
    jaw_half_angle: float = 30.
    contact_offset: float = .0126
    ring_thickness: float = .0016
    clearance: float = .0001
    sweep_step: float = .00075
    max_substeps: int = 64
    search_iterations: int = 9
    workspace_planes: tuple = ()  # Optional inward planes; legacy scenes unchanged.
    distal_length: float = .018
    ring_radius: float = .0071  # Outer radius, including torus thickness.


def transform(pose,vector):
    """Ry(yaw) Rx(pitch) Rz(roll), matching the existing trocar rig."""
    y,p,r=map(radians,(pose.yaw,pose.pitch,pose.rotation))
    x0,y0,z0=vector
    x1,y1=x0*cos(r)-y0*sin(r),x0*sin(r)+y0*cos(r)
    y2,z2=y1*cos(p)-z0*sin(p),y1*sin(p)+z0*cos(p)
    return (x1*cos(y)+z2*sin(y),y2,-x1*sin(y)+z2*cos(y))


def proxies(pivot,pose,cfg):
    base=add(pivot,transform(pose,(0,0,-pose.insertion)))
    segments=[(pivot,base,cfg.shaft_radius)]
    theta=radians(cfg.jaw_half_angle*pose.jaw)
    for sign in (-1,1):
        hinge=add(base,transform(pose,(sign*cfg.hinge_offset,0,0)))
        end=add(hinge,transform(pose,(sign*sin(theta)*cfg.jaw_length,0,-cos(theta)*cfg.jaw_length)))
        segments.append((hinge,end,cfg.jaw_radius))
    contact=add(base,transform(pose,(0,0,-cfg.contact_offset*cos(theta))))
    return segments,contact


class CollisionConstraint:
    def __init__(self,pivots,limits,settings=None):
        self.pivots=pivots; self.limits=limits; self.settings=settings or CollisionSettings()
        self.reset()

    def reset(self):
        self.contacts=set()
        self._cache={}

    def _geometry(self,side,pose):
        key=(side,pose)
        if key not in self._cache:
            self._cache[key]=proxies(self.pivots[side],pose,self.settings)
        return self._cache[key]

    def board_gap(self,side,pose,held):
        cfg=self.settings
        segments,contact=self._geometry(side,pose)
        lowest=min(min(a[2],b[2])-radius for a,b,radius in segments)
        if side in held:
            lowest=min(lowest,contact[2]+held[side][2]-cfg.ring_thickness)
        return lowest-cfg.board_height-cfg.clearance

    def pair_gap(self,poses):
        left=self._geometry('LEFT',poses['LEFT'])[0]
        right=self._geometry('RIGHT',poses['RIGHT'])[0]
        return min(segment_distance(a,b,c,d)-r-s-self.settings.clearance
                   for a,b,r in left for c,d,s in right)

    def _pair_clear(self,poses):
        left=self._geometry('LEFT',poses['LEFT'])[0]
        right=self._geometry('RIGHT',poses['RIGHT'])[0]
        # Reject immediately on the first overlapping capsule pair.
        return all(segment_distance(a,b,c,d)>=r+s+self.settings.clearance-1e-10
                   for a,b,r in left for c,d,s in right)

    def workspace_gaps(self,side,pose,held):
        cfg=self.settings
        if not cfg.workspace_planes: return {}
        segments,contact=self._geometry(side,pose)
        base=segments[0][1]
        distal=(add(base,transform(pose,(0,0,cfg.distal_length))),base,cfg.shaft_radius)
        working=(distal,*segments[1:])  # Proximal shaft/trocar intentionally outside.
        ring=add(contact,held[side]) if side in held else None
        gaps={}
        for name,n,offset in cfg.workspace_planes:
            low=min(min(dot(n,a),dot(n,b))-radius for a,b,radius in working)
            if ring is not None:
                support=cfg.ring_radius*hypot(n[0],n[1])+cfg.ring_thickness*abs(n[2])
                low=min(low,dot(n,ring)-support)
            gaps[name]=low-offset-cfg.clearance
        return gaps

    def workspace_gap(self,side,pose,held):
        return min(self.workspace_gaps(side,pose,held).values(),default=float('inf'))

    def _board_project(self,side,pose,held):
        gap=self.board_gap(side,pose,held)
        if gap<0:
            vertical=-transform(pose,(0,0,-1))[2]
            pose=replace(pose,insertion=max(self.limits.insertion[0],pose.insertion+gap/vertical))
        if self.settings.workspace_planes:
            # All working proxies translate together along the shaft when insertion
            # changes. Intersect their allowable insertion intervals to slide along
            # the wall without moving the pivot or disconnecting the jaws.
            low,high=self.limits.insertion
            direction=transform(pose,(0,0,-1))
            gaps=self.workspace_gaps(side,pose,held)
            for name,n,_ in self.settings.workspace_planes:
                slope=dot(n,direction)
                if slope>1e-10: low=max(low,pose.insertion-gaps[name]/slope)
                elif slope< -1e-10: high=min(high,pose.insertion-gaps[name]/slope)
            if low<=high:
                pose=replace(pose,insertion=min(high,max(low,pose.insertion)))
        return pose

    def resolve(self,previous,proposed,held=None):
        """Substep joint motion; slide at board and reject pair-penetrating axes.

        Accepted state is returned to the controller, so blocked intent never
        accumulates. No collision cache or sticky lock affects escape movement.
        held maps owner to the existing world-space grasp offset.
        """
        held=held or {}; cfg=self.settings; self.contacts=set(); self._cache={}
        proposed={s:p.limited(self.limits) for s,p in proposed.items()}
        # Conservative endpoint arc-length bound; no large jump through thin proxies.
        travel=max(abs(proposed[s].insertion-previous[s].insertion)+
                   (self.limits.insertion[1]+cfg.jaw_length)*radians(abs(proposed[s].yaw-previous[s].yaw)+abs(proposed[s].pitch-previous[s].pitch))+
                   cfg.jaw_length*radians(abs(proposed[s].rotation-previous[s].rotation)+cfg.jaw_half_angle*abs(proposed[s].jaw-previous[s].jaw))
                   for s in previous)
        count=max(1,ceil(travel/cfg.sweep_step))
        current=dict(previous)
        for step in range(1,min(count,cfg.max_substeps)+1):
            step_start=dict(current)
            for side in ('LEFT','RIGHT'):
                for channel in ('jaw','rotation','yaw','pitch','insertion'):
                    start=current[side]
                    desired=getattr(previous[side],channel)+(getattr(proposed[side],channel)-getattr(previous[side],channel))*step/count
                    if abs(desired-getattr(start,channel))<1e-12: continue
                    def candidate(fraction):
                        pose=replace(start,**{channel:getattr(start,channel)+(desired-getattr(start,channel))*fraction})
                        return self._board_project(side,pose,held)
                    pose=candidate(1.)
                    trial={**current,side:pose}
                    def valid(pose):
                        return ((not cfg.workspace_planes or abs(pose.insertion-start.insertion)<=cfg.sweep_step+1e-10)
                                and self.board_gap(side,pose,held)>=-1e-10
                                and self.workspace_gap(side,pose,held)>=-1e-10
                                and self._pair_clear({**current,side:pose}))
                    if valid(pose):
                        current=trial
                    else:
                        self.contacts.add(side+(':workspace' if self.workspace_gap(side,pose,held)<-1e-10 else ':instrument'))
                        low,high=0.,1.
                        for _ in range(cfg.search_iterations):
                            middle=(low+high)/2; pose=candidate(middle)
                            if valid(pose): low=middle
                            else: high=middle
                        current[side]=candidate(low) if low else start
                if self.board_gap(side,current[side],held)<1e-7: self.contacts.add(side+':board')
                for name,gap in self.workspace_gaps(side,current[side],held).items():
                    if gap<1e-7: self.contacts.add(side+':'+name)
            if current==step_start:
                break  # Remaining intent cannot cross contact; retry fresh next tick.
        return current
