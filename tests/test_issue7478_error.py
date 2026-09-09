"""Application-error settlement releases its owner without cutting recovery short."""
import pytest
from tests.test_issue6391_live_scene_paint import run_js


@pytest.mark.parametrize('lane', ['background', 'current', 'recovery', 'recovery-replaced'])
def test_application_error_releases_projection_owner(lane):
    run_js(r"""
(async()=>{
let _anchorPaintGeneration=0,_anchorPaintDisposed=false,_anchorPaintScheduler=null;
let _terminalStateReached=false,_streamFinalized=false,_persistTimer=null;
const activeSid='s',streamId='r',LIVE_STREAMS={},INFLIGHT={};
const S={session:{session_id:LANE==='background'?'other':'s'},messages:[],activeStreamId:'r'};
let assistantText='partial',closed=0,lifecycle=0;
const _anchorRegistry={};
const _anchorSceneRenderProjectionCaches=new Map([['live',{sessionId:'s',streamId:'r'}]]);
eval(extract(src,'_releaseAnchorSceneRenderProjections'));
const _disposeAnchorScenePaint=()=>{_anchorPaintGeneration++;_anchorPaintDisposed=true;_releaseAnchorSceneRenderProjections(activeSid,streamId);};
const snapshotLiveTurnHtmlForSession=()=>{},_resumeSessionStreamAfterLiveChat=()=>{};
eval(extract(messageSource,'closeLiveStream'));
const _closeSource=source=>closeLiveStream(activeSid,streamId,source);
const _bailOutOfTerminalEventsFromStaleStream=()=>false;
const _clearStreamEndRecovery=()=>{},_cancelThrottledSnapshotTimer=()=>{};
const _clearAnchorProseIncrementalNode=()=>{},_cancelAnimationFramePendingStreamRender=()=>{};
const _streamFadeCleanupReduceMotionListener=()=>{},_smdEndParser=()=>{};
const _clearOwnerInflightState=()=>{},_clearStreamHidden=()=>{},_clearStreamNotificationBackground=()=>{};
const _clearApprovalForOwner=()=>{},_clearClarifyForOwner=()=>{},_flushReasoningToAnchor=()=>{};
const _applyToAnchor=()=>{},_scheduleAnchorRegistryCleanup=()=>{},_drainSemanticProse=()=>{};
const _rememberRunJournalCursor=()=>{},_withDeferredAnchorScenePaint=fn=>fn;
const renderSessionList=()=>{},_setActivePaneIdleIfOwner=()=>{},trackBackgroundError=()=>{};
const _attachProjectedAnchorSceneToLastAssistant=()=>{},clearLiveToolCards=()=>{};
const _markSessionViewed=()=>{},renderMessages=()=>{},_settledAnchorRetryOwnerKey=()=>'';
const _filterRecoveryControlMessages=x=>x;
const _dispatchExtensionTurnLifecycle=()=>lifecycle++,_completeOwnedTerminal=()=>{};
const setTimeout=()=>1;
let resolveRecovery;
const _restoreSettledSession=()=>new Promise(resolve=>{resolveRecovery=resolve;});
const callbacks=[];
const source={readyState:1,close(){closed++;this.readyState=2;},addEventListener(type,fn){callbacks.push({type,fn});}};
eval(extract(messageSource,'_wireSSE'));_wireSSE(source);
const data=LANE.startsWith('recovery')?{session_id:'s',type:'interrupted',recovery_control:true}:{session_id:'s',type:'rate_limit',message:'synthetic error'};
for(const x of callbacks.filter(x=>x.type==='apperror')) x.fn({data:JSON.stringify(data)});
if(LANE.startsWith('recovery')){
 assert.equal(_anchorPaintDisposed,false,'recovery retains generation until settlement');
 assert.equal(_anchorSceneRenderProjectionCaches.size,1);
 assert.equal(typeof resolveRecovery,'function');
 if(LANE==='recovery-replaced') LIVE_STREAMS.s={streamId:'r',source:{readyState:1}};
 resolveRecovery(true);
 await new Promise(resolve=>setImmediate(resolve));
}
assert.equal(lifecycle,1);assert.equal(closed,1);
if(LANE==='recovery-replaced'){
 assert.notEqual(LIVE_STREAMS.s.source,source);
 assert.equal(_anchorSceneRenderProjectionCaches.size,1,'late recovery must not release successor state');
 return;
}
assert.equal(LIVE_STREAMS.s,undefined,'application error retires the closed owner');
assert.equal(_anchorPaintDisposed,true);assert.equal(_anchorSceneRenderProjectionCaches.size,0);
})().catch(error=>{console.error(error);process.exitCode=1;});
""".replace('LANE', repr(lane)))
