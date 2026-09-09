"""Producer semantic parsing batches tokens and drains at boundaries."""
from tests.test_issue6391_live_scene_paint import run_js
from tests.test_issue3455_think_block_extraction import _extract_block, MESSAGES_JS


def test_batched_prose_preserves_thinking_and_boundary_order():
    helpers = _extract_block(MESSAGES_JS, 'const _thinkPairs=') + ';\n'
    for name in ['_thinkingFenceMarkerAt', '_nextThinkingOpener', '_textTailIsPartialOpener', '_lineIsIndentedCode', '_mergeInlineThinkingReasoning', '_extractInlineThinkingFromContent']:
        helpers += _extract_block(MESSAGES_JS, 'function ' + name + '(') + '\n'
    run_js(helpers + r"""
let assistantText='',liveReasoningText='',segmentStart=0,_anchorPaintDisposed=false;
let _semanticProseTimer=null,_semanticProseDirty=false;
const setTimeout=()=>1,clearTimeout=()=>{};
const syncInflightAssistantMessage=()=>{},assistantRow={};
const _stripXmlToolCalls=x=>x;
const rows=[];
let proseRow=null;
const _upsertAnchorProcessProse=text=>{if(!proseRow){proseRow={role:'prose'};rows.push(proseRow);}proseRow.text=text;};
for(const f of ['_parseStreamState','_parseCurrentSegmentDisplayText','_drainSemanticProse','_scheduleSemanticProse']) eval(extract(messageSource,f));
assistantText='<thi';_scheduleSemanticProse();_drainSemanticProse();assert.equal(rows.length,0);
assistantText+='nk>private reasoning';_scheduleSemanticProse();_drainSemanticProse();assert.equal(rows.length,0);
assistantText+='</think>before';_scheduleSemanticProse();_drainSemanticProse();
assert.equal(rows[0].text,'before');assert.equal(_parseStreamState().thinkingText,'private reasoning');
rows.push({role:'tool',text:'work'});segmentStart=assistantText.length;proseRow=null;
assistantText+='after';_scheduleSemanticProse();_drainSemanticProse();
assert.deepEqual(rows.map(r=>[r.role,r.text]),[['prose','before'],['tool','work'],['prose','after']]);
assistantText+=' terminal';_scheduleSemanticProse();_drainSemanticProse();
assert.equal(rows[2].text,'after terminal');
assistantText+='<think>post-tool secret</think>visible';_scheduleSemanticProse();_drainSemanticProse();
assert.equal(rows[2].text,'after terminalvisible');
assert.equal(_semanticProseDirty,false);assert.equal(_semanticProseTimer,null);
""")


def test_semantic_prose_batches_long_token_burst_and_drains():
    run_js(r"""
let assistantText='',segmentStart=0,_anchorPaintDisposed=false;
let _semanticProseTimer=null,_semanticProseDirty=false;
let scans=0,prose='';
const setTimeout=()=>1,clearTimeout=()=>{};
const syncInflightAssistantMessage=()=>{},assistantRow={};
const _parseStreamState=()=>{scans++;return {displayText:assistantText};};
const _stripXmlToolCalls=x=>x;
const _upsertAnchorProcessProse=x=>{prose=x;};
for(const f of ['_drainSemanticProse','_scheduleSemanticProse']) eval(extract(messageSource,f));
for(let i=0;i<10000;i++){assistantText+='x';_scheduleSemanticProse();}
assert.equal(scans,0);
_drainSemanticProse();
assert.equal(scans,1);assert.equal(prose.length,10000);
_drainSemanticProse();assert.equal(scans,1);
""")
