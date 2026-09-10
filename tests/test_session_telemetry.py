"""Deterministic simulator observations, no camera/Blender/wall-clock dependence."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import unittest
from lapsim_ai.telemetry.session import SessionTelemetry


def observe(t,owner=None,placement='SOURCE',state='RUNNING',dt=1,paused=False,left=(0,0,0),right=(0,0,0)):
    t.observe(dt=dt,paused=paused,task_state=state,owners={'ring':owner},
              placements={'ring':placement},completed=int(placement=='CORRECT'),tips={'LEFT':left,'RIGHT':right})


class SessionTests(unittest.TestCase):
    def test_start_time_pause_paths_and_completion(self):
        t=SessionTelemetry('peg_transfer',1)
        observe(t,state='READY',left=(2,0,0))
        self.assertIsNone(t.started)
        observe(t,'LEFT','HELD',left=(3,0,0))
        self.assertEqual(t.paths['LEFT'],0)
        observe(t,'LEFT','HELD',left=(3.1,0,0),right=(0,.2,0))
        self.assertAlmostEqual(t.paths['LEFT'],.1); self.assertAlmostEqual(t.paths['RIGHT'],.2)
        observe(t,'LEFT','HELD',paused=True,dt=5,left=(8,0,0))
        observe(t,'LEFT','HELD',left=(9,0,0))
        self.assertAlmostEqual(t.paths['LEFT'],.1)
        observe(t,None,'CORRECT',state='COMPLETE',left=(9.1,0,0))
        result=t.result
        self.assertEqual(result['active_seconds'],4)
        self.assertEqual(result['paused_seconds'],5)
        self.assertAlmostEqual(result['path_metres']['TOTAL'],.4)
        self.assertEqual(len(result['pause_intervals']),1)
        self.assertEqual(result['counts']['grasps'],1)
        self.assertEqual(result['counts']['releases'],1)
        self.assertEqual(result['counts']['successful_placements'],1)
        self.assertEqual(result['outcome'],'COMPLETE')
        self.assertEqual(result['end_seconds']-result['start_seconds'],9)
        self.assertEqual(result['events'][0]['time_seconds'],result['start_seconds'])
        json.dumps(result,allow_nan=False)
        result['counts']['grasps']=99
        observe(t,dt=100)
        self.assertEqual(t.result['counts']['grasps'],1)
        self.assertEqual(t.active,4)

    def test_events_handoff_wrong_drop_repeat_and_reset(self):
        def run():
            t=SessionTelemetry('peg_transfer',1)
            for owner,placement,state in [('LEFT','HELD','RUNNING'),('RIGHT','HELD','RUNNING'),
                (None,'INCORRECT','RUNNING'),(None,'INCORRECT','RUNNING'),('RIGHT','HELD','RUNNING'),
                (None,'DROPPED','RUNNING'),('LEFT','HELD','RUNNING'),(None,'CORRECT','COMPLETE')]:
                observe(t,owner,placement,state)
            return t
        t=run()
        self.assertEqual(t.result,run().result)
        self.assertEqual(t.counts,dict(grasps=4,releases=4,handoffs=1,drops=1,incorrect_placements=1,successful_placements=1))
        kinds=[e['type'] for e in t.result['events']]
        for event in ('session_start','session_end','ownership_change','grasp','release','handoff','drops','incorrect_placements','successful_placements','task_complete'):
            self.assertIn(event,kinds)
        t.reset()
        self.assertIsNone(t.result); self.assertIsNone(t.started)
        self.assertEqual(sum(t.paths.values())+sum(t.counts.values())+t.active,0)
        self.assertFalse(t.samples or t.events or t.pauses or t.anchors or t.owners)
        observe(t,'RIGHT','HELD')
        self.assertEqual(t.counts['grasps'],1)

    def test_noise_threshold_and_independent_motion(self):
        t=SessionTelemetry('test',1)
        observe(t,'LEFT','HELD')
        for i in range(100):
            observe(t,'LEFT','HELD',dt=.01,left=(.0002*(-1)**i,0,0))
        self.assertEqual(t.paths,{'LEFT':0.,'RIGHT':0.})
        for i in range(1,11):
            observe(t,'LEFT','HELD',dt=.01,left=(i*.0001,0,0))
        self.assertAlmostEqual(t.paths['LEFT'],.001)
        self.assertEqual(t.paths['RIGHT'],0)

    def test_stop_pause_and_bounded_storage(self):
        t=SessionTelemetry('test',1)
        observe(t,'LEFT','HELD')
        for _ in range(605): observe(t,'LEFT','HELD',dt=.2)
        self.assertEqual(len(t.samples),600)
        self.assertTrue(t.truncated['samples'])
        observe(t,'LEFT','HELD',paused=True,dt=2)
        t.finish(0)
        self.assertEqual(t.result['outcome'],'STOPPED')
        self.assertEqual(t.result['paused_seconds'],2)
        snapshot=t.result; t.finish(1)
        self.assertEqual(t.result,snapshot)


if __name__=='__main__': unittest.main()
