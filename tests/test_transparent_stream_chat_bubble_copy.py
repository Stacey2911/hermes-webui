"""Regression coverage for Transparent Stream chat-bubble copy affordance."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
UI_JS_PATH = ROOT / "static" / "ui.js"
STYLE_CSS_PATH = ROOT / "static" / "style.css"
UI_JS = UI_JS_PATH.read_text(encoding="utf-8")
STYLE_CSS = STYLE_CSS_PATH.read_text(encoding="utf-8")
NODE = shutil.which("node")


def _function_body(src: str, name: str) -> str:
    start = src.index(f"function {name}")
    brace = src.index("{", start)
    depth = 1
    pos = brace + 1
    while depth and pos < len(src):
        if src[pos] == "{":
            depth += 1
        elif src[pos] == "}":
            depth -= 1
        pos += 1
    return src[start:pos]


def test_transparent_ordered_text_part_receives_normal_message_footer_copy_button():
    ordered_start = UI_JS.index("if(Array.isArray(orderedTransparentParts)&&orderedTransparentParts.length){")
    ordered_end = UI_JS.index("seg.className='assistant-segment';", ordered_start)
    ordered_block = UI_JS[ordered_start:ordered_end]

    assert 'const copyBtn  = `<button class="msg-copy-btn msg-action-btn"' in UI_JS
    assert 'const footHtml = `<div class="msg-foot">' in UI_JS
    assert "orderedSeg.dataset.rawText=String(partDisplayText||'').trim();" in ordered_block
    assert "const isLastTextPart=partIdx===lastTextPartIdx;" in ordered_block
    assert "`${isLastTextPart?filesHtml:''}<div class=\"msg-body\">${partBodyHtml}</div>${isLastTextPart?footHtml:''}`" in ordered_block


def test_transparent_chat_bubble_click_reveal_is_wired_for_fresh_and_cached_dom():
    reveal_fn = _function_body(UI_JS, "_wireTransparentMessageActionReveal")
    rehydrate_fn = _function_body(UI_JS, "_rehydrateTransparentStreamDom")
    render_wiring_start = UI_JS.index("if(isTransparentStream()){", UI_JS.index("// Transparent mode per-turn wiring:"))
    render_wiring_end = UI_JS.index("// Fail-safe invariant", render_wiring_start)
    render_wiring = UI_JS[render_wiring_start:render_wiring_end]

    assert "if(!root||!isTransparentStream()) return;" in reveal_fn
    assert "if(turn.id==='liveAssistantTurn') return;" in reveal_fn
    assert "turn.addEventListener('click'" in reveal_fn
    assert "target.closest('.msg-action-btn,.msg-foot,.transparent-event-row,.transparent-turn-footer,.msg-role.assistant')" in reveal_fn
    assert "if(!turn.querySelector('.msg-foot .msg-copy-btn')) return;" in reveal_fn
    assert "turn.setAttribute('data-transparent-msg-actions-open','1');" in reveal_fn
    assert "_wireTransparentMessageActionReveal(root);" in rehydrate_fn
    assert "_wireTransparentMessageActionReveal(inner);" in render_wiring


def test_transparent_click_reveal_css_keeps_existing_hover_and_focus_behavior():
    assert ".assistant-turn:hover .msg-foot," in STYLE_CSS
    assert ".assistant-turn:focus-within .msg-foot," in STYLE_CSS
    assert '.assistant-turn[data-transparent-msg-actions-open="1"] .msg-foot { opacity: 1; }' in STYLE_CSS
    assert '.assistant-turn[data-transparent-msg-actions-open="1"] .msg-foot-with-usage .msg-actions' in STYLE_CSS
    assert '.assistant-turn[data-transparent-msg-actions-open="1"] .msg-foot:has(.msg-question-jump-btn) .msg-actions' in STYLE_CSS


def test_transparent_click_reveal_does_not_create_duplicate_copy_controls():
    reveal_fn = _function_body(UI_JS, "_wireTransparentMessageActionReveal")

    assert "createElement('button')" not in reveal_fn
    assert "transparent-event-copy" not in reveal_fn
    assert "thinking-copy-btn" not in reveal_fn
    assert "msg-copy-btn" in reveal_fn


@pytest.mark.skipif(NODE is None, reason="node not on PATH")
def test_message_copy_button_invokes_copy_helper_with_raw_assistant_text():
    driver = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function extractFunc(name) {
  const start = src.indexOf('function ' + name);
  if (start < 0) throw new Error(name + ' not found');
  let i = src.indexOf('{', start) + 1;
  let depth = 1;
  while (depth > 0 && i < src.length) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') depth--;
    i++;
  }
  return src.slice(start, i);
}
let copied = null;
global._copyText = text => {
  copied = text;
  return { then(cb){ cb(); return { catch(){} }; } };
};
global.li = () => 'ok';
global.showToast = () => {};
global.t = key => key;
eval(extractFunc('copyMsg'));
const row = { dataset: { rawText: 'assistant answer text' } };
const btn = {
  innerHTML: 'copy',
  style: {},
  closest(selector) {
    if (selector === '[data-raw-text]') return row;
    return null;
  },
};
copyMsg(btn);
process.stdout.write(JSON.stringify({ copied }));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(driver)
        script_path = Path(handle.name)
    try:
        result = subprocess.run(
            [NODE, str(script_path), str(UI_JS_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    finally:
        script_path.unlink(missing_ok=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["copied"] == "assistant answer text"
