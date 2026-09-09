"""Payload-less cancellation keeps its async canonical settlement owner."""
import pytest
from tests.test_issue6391_live_scene_paint import run_js


@pytest.mark.parametrize('has_row', [True, False])
def test_wire_cancel_awaits_canonical_snapshot(has_row):
    run_js(r"""
(async()=>{
let _anchorPaintGeneration=0,_anchorPaintDisposed=false,_anchorPaintScheduler=null;
let _terminalStateReached=false,_streamFinalized=false,_persistTimer=null;
const activeSid='s',streamId='r',LIVE_STREAMS={};
const S={session:{session_id:'s'},messages:[],activeStreamId:'r'};
let assistantText='partial',closed=0,lifecycle=0,rendered=0;
let segmentStart=0,_semanticProseTimer=null,_semanticProseDirty=false,scans=0,semanticText='';
const setTimeout=()=>1,clearTimeout=()=>{};
const assistantRow=ASSISTANT_ROW,_freshSegment=false;
let inflightScans=0;
const syncInflightAssistantMessage=()=>{inflightScans++;},_completeAutomaticCompressionOnLiveProgress=()=>{};
const ensureAssistantRow=()=>{},_scheduleRender=()=>{};
const _parseStreamState=()=>{scans++;return {displayText:assistantText};};
const _stripXmlToolCalls=x=>x,_upsertAnchorProcessProse=x=>{semanticText=x;};
for(const f of ['_drainSemanticProse','_scheduleSemanticProse']) eval(extract(messageSource,f));
let resolveFetch; const api=()=>new Promise(resolve=>{resolveFetch=resolve;});
const _bailOutOfTerminalEventsFromStaleStream=()=>false;
const _clearStreamEndRecovery=()=>{},_cancelThrottledSnapshotTimer=()=>{};
const _clearAnchorProseIncrementalNode=()=>{},_cancelAnimationFramePendingStreamRender=()=>{};
const _streamFadeCleanupReduceMotionListener=()=>{},_smdEndParser=()=>{};
const _clearOwnerInflightState=()=>{},_clearStreamHidden=()=>{},_clearStreamNotificationBackground=()=>{};
const _clearApprovalForOwner=()=>{},_clearClarifyForOwner=()=>{},_flushReasoningToAnchor=()=>{};
const _applyToAnchor=()=>{},_scheduleAnchorRegistryCleanup=()=>{};
const _rememberRunJournalCursor=()=>{},_withDeferredAnchorScenePaint=fn=>fn;
const renderSessionList=()=>{},_setActivePaneIdleIfOwner=()=>{};
const _attachProjectedAnchorSceneToLastAssistant=()=>{};
const _carryForwardEphemeralTurnFields=(_,messages)=>messages;
const clearLiveToolCards=()=>{},_markSessionViewed=()=>{};
const renderMessages=()=>rendered++;
const _dispatchExtensionTurnLifecycle=type=>{assert.equal(type,'turn:cancel');lifecycle++;};
const _completeOwnedTerminal=()=>{};
const _closeSource=()=>{_anchorPaintGeneration++;_anchorPaintDisposed=true;delete LIVE_STREAMS.s;};
const callbacks=[];
const source={readyState:1,close(){closed++;this.readyState=2;},addEventListener(type,fn){callbacks.push({type,fn});}};
eval(extract(messageSource,'_wireSSE')); _wireSSE(source);
for(let i=0;i<10000;i++) for(const x of callbacks.filter(x=>x.type==='token')) x.fn({data:'{"text":"x"}'});
assert.equal(scans,0,'the actual token handler must not scan full history');
assert.equal(inflightScans,0,'inflight thinking extraction must also be batched');
for(const x of callbacks.filter(x=>x.type==='cancel')) x.fn({data:'{}'});
assert.equal(scans,1,'terminal boundary drains the coalesced semantic state');
assert.equal(semanticText,assistantText);
for(const x of callbacks.filter(x=>x.type==='stream_end')) x.fn({data:'{}'});
assert.equal(_anchorPaintDisposed,false,'auxiliary cancel must not dispose pending canonical settlement');
assert.equal(typeof resolveFetch,'function');
resolveFetch({session:{session_id:'s',messages:[{role:'assistant',content:'canonical partial',_partial:true}]}});
await new Promise(resolve=>setImmediate(resolve));
assert.equal(S.messages[0].content,'canonical partial');
assert.equal(rendered,1);assert.equal(lifecycle,1);assert.equal(closed,1);
assert.equal(LIVE_STREAMS.s,undefined);
})().catch(error=>{console.error(error);process.exitCode=1;});
""".replace('ASSISTANT_ROW', '{}' if has_row else 'null'))
