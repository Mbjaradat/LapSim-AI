"""Deterministic peg task layered on the existing grasp model; no input or bpy."""
from math import dist, isfinite
from lapsim_ai.simulator.grasp import GraspWorld


class PegTransfer:
    def __init__(self, sources, targets, *, seat_height, placement_radius=.006,
                 placement_height=.012):
        if not sources or set(sources) != set(targets):
            raise ValueError('Each object requires one source and matching target')
        self.world = GraspWorld(sources)
        self.targets = {name:tuple(p) for name,p in targets.items()}
        self.seat_height = seat_height
        self.placement_radius = placement_radius
        self.placement_height = placement_height
        self.reset()

    def reset(self):
        self.world.reset()
        self.pending = {}
        self.placements = {name:'SOURCE' for name in self.world.homes}
        self.state = 'READY'
        self.elapsed = 0.

    @property
    def completed(self):
        return sum(value == 'CORRECT' for value in self.placements.values())

    def _place(self, name):
        point = self.world.positions[name]
        candidates = []
        for kind, locations in (('TARGET',self.targets), ('SOURCE',self.world.homes)):
            for peg, seat in locations.items():
                if (dist(point[:2],seat[:2]) <= self.placement_radius
                        and abs(point[2]-seat[2]) <= self.placement_height):
                    occupied = any(other != name and self.world.owners[other] is None
                                   and dist(pos,seat) < self.placement_radius
                                   for other,pos in self.world.positions.items())
                    if not occupied:
                        candidates.append((dist(point,seat),kind,peg,seat))
        if candidates:
            _,kind,peg,seat = min(candidates)
            self.world.positions[name] = seat
            self.placements[name] = ('SOURCE' if kind == 'SOURCE' else
                                     'CORRECT' if peg == name else 'INCORRECT')
        else:
            # Lightweight drop: settle vertically onto the support plane, no bounce.
            # Avoid leaving a dropped ring coincident with an occupied peg/ring.
            offsets = [(0,0)] + [(dx*r,dy*r) for r in (.012,.024,.036)
                                 for dx,dy in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1))]
            for dx,dy in offsets:
                xy = (point[0]+dx,point[1]+dy)
                if (all(dist(xy,p[:2]) >= .008 for p in (*self.targets.values(),*self.world.homes.values()))
                        and all(other == name or self.world.owners[other] is not None or dist(xy,p[:2]) >= .014
                                for other,p in self.world.positions.items())):
                    point = (*xy,point[2])
                    break
            self.world.positions[name] = (*point[:2],self.seat_height)
            self.placements[name] = 'DROPPED'

    def update(self, hands, dt):
        if not isfinite(dt) or dt < 0:
            raise ValueError('dt must be finite and nonnegative')
        if self.state == 'COMPLETE':
            return dict(self.world.positions)  # Explicit reset starts the next trial.
        safe = {side:(tuple(p),jaw) for side,(p,jaw) in hands.items()
                if side in ('LEFT','RIGHT') and len(p)==3
                and all(isfinite(v) for v in (*p,jaw)) and 0 <= jaw <= 1}
        before = dict(self.world.owners)
        previous_jaw = dict(self.world.previous_jaw)
        self.world.update(safe)
        cfg = self.world.settings
        # Arm the nearest held object on a receiver's closing edge. Donor retains
        # sole ownership until opening. Already-closed receivers must reopen first.
        for side,(point,jaw) in sorted(safe.items()):
            if side in self.world.owners.values():
                continue
            if jaw <= cfg.close_threshold < previous_jaw[side]:
                candidates = [(dist(point,self.world.positions[name]),name)
                              for name,owner in before.items() if owner and owner != side
                              and dist(point,self.world.positions[name]) <= cfg.capture_distance]
                if candidates:
                    self.pending[min(candidates)[1]] = side
        for name,receiver in list(self.pending.items()):
            observation = safe.get(receiver)
            if (observation is None or observation[1] > cfg.close_threshold
                    or receiver in self.world.owners.values()
                    or dist(observation[0],self.world.positions[name]) > cfg.capture_distance):
                del self.pending[name]
                continue
            if before[name] is not None and self.world.owners[name] is None:
                self.world.owners[name] = receiver
                self.world.offsets[name] = tuple(v-p for v,p in zip(self.world.positions[name],observation[0]))
                del self.pending[name]
        for name,owner in self.world.owners.items():
            if owner:
                self.placements[name] = 'HELD'
                if self.state == 'READY': self.state = 'RUNNING'
            elif before[name] is not None:
                self._place(name)
        if self.state == 'RUNNING':
            self.elapsed += dt
            if self.completed == len(self.targets): self.state = 'COMPLETE'
        return dict(self.world.positions)
