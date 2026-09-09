"""Small deterministic rigid-token grasp model; no physics, bpy or input code."""
from dataclasses import dataclass
from math import dist, isfinite


@dataclass(frozen=True)
class GraspSettings:
    capture_distance: float = .009
    close_threshold: float = .25
    release_threshold: float = .65


class GraspWorld:
    def __init__(self, homes, settings=None):
        self.settings=settings or GraspSettings()
        self.homes={name:tuple(point) for name,point in homes.items()}
        self.reset()

    def reset(self):
        self.positions=dict(self.homes)
        self.owners={name:None for name in self.homes}
        self.offsets={}
        self.previous_jaw={'LEFT':1.0,'RIGHT':1.0}

    def update(self, hands):
        """hands: side -> (contact xyz, jaw). Missing sides hold owned objects.

        Capture on a close-threshold crossing near the object centre. Release
        above the open threshold; preserve the capture offset (no snap). Sphere
        tokens follow translation only. Nearest pair wins, ties name then side.
        """
        safe={side:(tuple(point),jaw) for side,(point,jaw) in hands.items()
              if side in self.previous_jaw and len(point)==3
              and all(isfinite(v) for v in (*point,jaw)) and 0 <= jaw <= 1}
        cfg=self.settings
        for name,side in list(self.owners.items()):
            if side in safe:
                point,jaw=safe[side]
                self.positions[name]=tuple(v+o for v,o in zip(point,self.offsets[name]))
                if jaw >= cfg.release_threshold:
                    self.owners[name]=None
                    del self.offsets[name]
        occupied=set(self.owners.values())-{None}
        candidates=[]
        for side,(point,jaw) in safe.items():
            if side not in occupied and jaw <= cfg.close_threshold < self.previous_jaw[side]:
                candidates.extend((dist(point,pos),name,side) for name,pos in self.positions.items()
                                  if self.owners[name] is None and dist(point,pos) <= cfg.capture_distance)
        for _,name,side in sorted(candidates):
            if self.owners[name] is None and side not in occupied:
                self.owners[name]=side
                self.offsets[name]=tuple(v-p for v,p in zip(self.positions[name],safe[side][0]))
                occupied.add(side)
        for side,(_,jaw) in safe.items():
            self.previous_jaw[side]=jaw
        return dict(self.positions)
