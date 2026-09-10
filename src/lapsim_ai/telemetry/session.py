"""Bounded, input/render-independent observation of simulator sessions."""
from collections import deque
from copy import deepcopy
from math import dist, isfinite


class SessionTelemetry:
    def __init__(self,task_name,total,path_threshold=.0005):
        if total<1 or not isfinite(path_threshold) or path_threshold<=0:
            raise ValueError('Positive object count and path threshold required')
        self.task_name,self.total,self.path_threshold=task_name,total,path_threshold
        self.reset()

    def reset(self):
        self.clock=self.active=self.paused_seconds=0.
        self.started=self.ended=self.pause_start=None
        self.paths={'LEFT':0.,'RIGHT':0.}
        self.anchors={}
        self.owners={}
        self.counts={key:0 for key in ('grasps','releases','handoffs','drops','incorrect_placements','successful_placements')}
        self.events=deque(maxlen=4096)
        self.samples=deque(maxlen=600)
        self.pauses=deque(maxlen=1024)
        self.truncated={'events':False,'samples':False,'pauses':False}
        self.next_sample=0.
        self._result=None

    def _append(self,collection,value):
        target=getattr(self,collection)
        if len(target)==target.maxlen: self.truncated[collection]=True
        target.append(value)

    def _event(self,kind,time_seconds=None,**fields):
        self._append('events',dict(type=kind,time_seconds=self.clock if time_seconds is None else time_seconds,**fields))

    @property
    def result(self):
        return deepcopy(self._result)

    def observe(self,*,dt,paused,task_state,owners,placements,completed,tips):
        """One accepted simulator update. Times/coordinates are seconds/metres.

        Start includes the first-grasp update interval, matching the task timer.
        Pre-grasp motion is excluded. Pauses are sampled intervals, not UI events.
        """
        if not isfinite(dt) or dt<0 or set(tips)!={'LEFT','RIGHT'} or any(
                len(p)!=3 or not all(isfinite(v) for v in p) for p in tips.values()):
            raise ValueError('Finite dt and both finite 3D tip positions required')
        if self._result is not None: return
        self.clock+=dt
        if self.started is None:
            if paused or task_state not in ('RUNNING','COMPLETE'):
                self.owners=dict(owners)
                return
            self.started=self.clock-dt
            self._event('session_start',time_seconds=self.started)
            self.anchors={s:tuple(p) for s,p in tips.items()}
        if paused:
            if self.pause_start is None:
                self.pause_start=self.clock-dt
                self._event('pause_start',time_seconds=self.pause_start)
            self.anchors={s:tuple(p) for s,p in tips.items()}
            return
        resumed=self.pause_start is not None
        if resumed:
            self.paused_seconds+=self.clock-dt-self.pause_start
            self._append('pauses',dict(start_seconds=self.pause_start,end_seconds=self.clock-dt))
            self.pause_start=None
            self._event('pause_end',time_seconds=self.clock-dt)
            self.anchors={s:tuple(p) for s,p in tips.items()}
        self.active+=dt
        for side,point in tips.items():
            movement=dist(self.anchors[side],point)
            if movement>=self.path_threshold:
                self.paths[side]+=movement
                self.anchors[side]=tuple(point)
        if self.clock>=self.next_sample:
            self._append('samples',dict(time_seconds=self.clock,active_seconds=self.active,
                                       tips_metres={s:list(p) for s,p in tips.items()}))
            self.next_sample=self.clock+.1
        for name,new in sorted(owners.items()):
            old=self.owners.get(name)
            if old==new: continue
            self._event('ownership_change',object=name,previous_owner=old,owner=new)
            if old:
                self.counts['releases']+=1
                self._event('release',object=name,side=old)
            if new:
                self.counts['grasps']+=1
                self._event('grasp',object=name,side=new)
            if old and new:
                self.counts['handoffs']+=1
                self._event('handoff',object=name,donor=old,receiver=new)
            elif old:
                kind={'DROPPED':'drops','INCORRECT':'incorrect_placements','CORRECT':'successful_placements'}.get(placements[name])
                if kind:
                    self.counts[kind]+=1
                    self._event(kind,object=name)
        self.owners=dict(owners)
        if task_state=='COMPLETE':
            self._event('task_complete')
            self.finish(completed,'COMPLETE')

    def finish(self,completed,outcome='STOPPED'):
        """End an observed session at its last sample; repeated calls are harmless."""
        if self.started is None or self._result is not None: return
        if self.pause_start is not None:
            self.paused_seconds+=self.clock-self.pause_start
            self._append('pauses',dict(start_seconds=self.pause_start,end_seconds=self.clock))
            self.pause_start=None
            self._event('pause_end')
        self.ended=self.clock
        self._event('session_end',outcome=outcome)
        self._result=dict(schema_version=1,task=self.task_name,outcome=outcome,
                start_seconds=self.started,end_seconds=self.ended,active_seconds=self.active,
                paused_seconds=self.paused_seconds,
                objects_completed=completed,objects_total=self.total,
                counts=dict(self.counts),path_metres={**self.paths,'TOTAL':sum(self.paths.values())},
                path_threshold_metres=self.path_threshold,
                pause_intervals=list(self.pauses),events=list(self.events),tip_samples=list(self.samples),
                truncated=dict(self.truncated))
