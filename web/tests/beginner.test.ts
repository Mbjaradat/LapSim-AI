import {test} from 'node:test';
import assert from 'node:assert/strict';
import {BeginnerTransfer} from '../src/beginner';
import {Session} from '../src/session';
import {sources,targets} from '../src/task';
import {inverseContact,type Side} from '../src/core';

for(const side of ['LEFT','RIGHT'] as Side[])test(`beginner: ${side}, any ring/target, no handoff, exactly one transfer`,()=>{
 for(const ring of Object.keys(sources))for(const target of Object.values(targets)){
  const task=new BeginnerTransfer();task.update({[side]:[sources[ring],0]},.05);
  assert.equal(task.owners[ring],side);task.update({[side]:[target,0]},.05);task.update({[side]:[target,1]},.05);
  assert.equal(task.completed,1);assert.equal(task.placements[ring],'CORRECT');
  for(let i=0;i<5;i++)task.update({[side]:[target,1]},.05);assert.equal(task.completed,1);
 }
});
function placed(){const t=new BeginnerTransfer();t.update({LEFT:[sources.RING_1,0]},.05);t.update({LEFT:[targets.RING_6,0]},.05);t.update({LEFT:[targets.RING_6,1]},.05);return t;}
test('beginner: clear confirmation then deterministic safe recycle; continued play beyond six',()=>{
 const a=placed(),b=placed();a.update({},.6);assert.deepEqual(a.positions.RING_1,targets.RING_6);a.update({},.61);b.update({},1.21);
 assert.deepEqual(a.positions,b.positions);assert.deepEqual(a.positions.RING_1,sources.RING_1);assert.equal(a.completed,1);
 for(let i=0;i<8;i++){a.update({RIGHT:[a.positions.RING_1,0]},.05);a.update({RIGHT:[targets.RING_2,0]},.05);a.update({RIGHT:[targets.RING_2,1]},.05);a.update({},1.3);}
 assert.equal(a.completed,9);assert.equal(a.state,'RUNNING');
});
test('beginner: recycle never teleports a held ring or interferes with held source ring',()=>{
 const t=placed();t.update({RIGHT:[targets.RING_6,0]},.05);const before=[...t.positions.RING_1];t.update({},2);assert.deepEqual(t.positions.RING_1,before);assert.equal(t.owners.RING_1,'RIGHT');
 const blocked=placed();blocked.owners.RING_2='RIGHT';blocked.positions.RING_2=[...sources.RING_1];blocked.offsets.RING_2=[0,0,0];blocked.update({},2);
 assert.notDeepEqual(blocked.positions.RING_1,sources.RING_1);assert.equal(blocked.owners.RING_2,'RIGHT');
 const moving=placed();moving.owners.RING_2='RIGHT';moving.positions.RING_2=[0,.08,-.11];moving.offsets.RING_2=[-.009,0,0];
 moving.update({RIGHT:[[-.012,.020,-.110],0]},2);assert.notDeepEqual(moving.positions.RING_1,sources.RING_1);
});
test('beginner: drop and returning to source do not increment transfers',()=>{
 const t=new BeginnerTransfer();t.update({LEFT:[sources.RING_3,0]},.05);t.update({LEFT:[[0,.08,-.11],0]},.05);t.update({LEFT:[[0,.08,-.11],1]},.05);assert.equal(t.placements.RING_3,'DROPPED');assert.equal(t.completed,0);
 t.update({RIGHT:[sources.RING_4,0]},.05);t.update({RIGHT:[sources.RING_4,1]},.05);assert.equal(t.completed,0);
});
function started(){const s=new Session('beginner');s.tick(0);s.gate.started=true;s.poses.LEFT=inverseContact('LEFT',sources.RING_1);s.task.update({LEFT:[sources.RING_1,0]},0);s.tick(.05);return s;}
test('beginner: setup, ready countdown and LIVE waiting consume no time; first grasp starts',()=>{
 const s=new Session('beginner');s.tick(0);s.tick(50);assert.equal(s.remaining,120);assert.equal(s.telemetry.started,null);s.gate.started=true;s.tick(70);assert.equal(s.remaining,120);
 const active=started();assert.notEqual(active.telemetry.started,null);assert.equal(active.telemetry.counts.grasps,1);assert.equal(active.remaining,119.95);
});
test('beginner: pause exclusion, exact expiry freezes poses/task/results, retry retains calibration',()=>{
 const s=started();s.paused=true;s.tick(10);assert.equal(s.telemetry.active,.05);s.paused=false;s.tick(11);
 s.setup.home={LEFT:[.3,.5],RIGHT:[.7,.5]};s.stabilizer.hands.LEFT.cal.open=.1;
 const calibration=structuredClone(s.stabilizer.hands.LEFT.cal),home=structuredClone(s.setup.home);
 s.tick(150);assert.equal(s.state,'COMPLETE');assert.equal(s.telemetry.result?.active_seconds,120);assert.equal(s.telemetry.result?.task,'beginner_free_transfer');
 const snapshot=structuredClone({poses:s.poses,positions:s.task.positions,result:s.telemetry.result});s.tick(200);s.task.update({RIGHT:[sources.RING_2,0]},.1);
 assert.deepEqual({poses:s.poses,positions:s.task.positions,result:s.telemetry.result},snapshot);
 s.retry();assert.equal(s.remaining,120);assert.equal(s.task.completed,0);assert.equal(s.telemetry.result,null);assert.equal(s.telemetry.counts.grasps,0);assert.deepEqual(s.task.positions,sources);assert.deepEqual(s.stabilizer.hands.LEFT.cal,calibration);assert.deepEqual(s.setup.home,home);assert.equal(s.gate.started,false);
});
