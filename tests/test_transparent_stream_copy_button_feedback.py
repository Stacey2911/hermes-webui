"""Regression coverage for Transparent Stream copy-button copied feedback."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
UI_JS_PATH = ROOT / "static" / "ui.js"
NODE = shutil.which("node")


def _run_node_script(script: str):
    assert NODE, "node is required for transparent stream copy feedback tests"
    env = os.environ.copy()
    env["UI_JS_PATH"] = str(UI_JS_PATH)
    result = subprocess.run(
        [NODE, "-e", script],
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


NODE_DRIVER_PREFIX = r"""
const fs = require('fs');
const src = fs.readFileSync(process.env.UI_JS_PATH, 'utf8');
function extractFunc(name) {
  const marker = new RegExp('function\\s+' + name + '\\s*\\(');
  const start = src.search(marker);
  if (start < 0) throw new Error(name + ' not found');
  let i = src.indexOf('{', start) + 1;
  let depth = 1;
  while (depth > 0 && i < src.length) {
    if (src[i] === '{') depth += 1;
    else if (src[i] === '}') depth -= 1;
    i += 1;
  }
  return src.slice(start, i);
}
class FakeElement {
  constructor(tag = 'div') {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.parentNode = null;
    this.attributes = Object.create(null);
    this.dataset = Object.create(null);
    this.style = Object.create(null);
    this.title = '';
    this.onclick = null;
    this.onkeydown = null;
    this._textContent = '';
    this._innerHTML = '';
    this._classes = new Set();
    const self = this;
    this.classList = {
      add(...names) { names.forEach(name => self._classes.add(name)); },
      remove(...names) { names.forEach(name => self._classes.delete(name)); },
      contains(name) { return self._classes.has(name); },
    };
  }
  get className() {
    return Array.from(this._classes).join(' ');
  }
  set className(value) {
    this._classes = new Set(String(value || '').trim().split(/\s+/).filter(Boolean));
  }
  get textContent() {
    return this._textContent;
  }
  set textContent(value) {
    this._textContent = String(value ?? '');
    this._innerHTML = this._textContent;
    this.children = [];
  }
  get innerHTML() {
    return this._innerHTML;
  }
  set innerHTML(value) {
    this._innerHTML = String(value ?? '');
    this._textContent = this._innerHTML;
    this.children = [];
  }
  setAttribute(name, value) {
    const key = String(name);
    const val = String(value);
    this.attributes[key] = val;
    if (key.startsWith('data-')) {
      const dataKey = key.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      this.dataset[dataKey] = val;
    }
    if (key === 'class') this.className = val;
  }
  getAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attributes, name) ? this.attributes[name] : null;
  }
  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }
  insertBefore(child, before) {
    child.parentNode = this;
    const idx = this.children.indexOf(before);
    if (idx < 0) this.children.push(child);
    else this.children.splice(idx, 0, child);
    return child;
  }
  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }
  querySelectorAll(selector) {
    const out = [];
    const walk = (node) => {
      for (const child of node.children) {
        if (matchesSelector(child, selector)) out.push(child);
        walk(child);
      }
    };
    walk(this);
    return out;
  }
  closest(selector) {
    let node = this;
    while (node) {
      if (matchesSelector(node, selector)) return node;
      node = node.parentNode;
    }
    return null;
  }
}
function matchesSelector(el, selector) {
  return String(selector || '').split(',').map(part => part.trim()).filter(Boolean).some(part => {
    const clsMatches = part.match(/\.([A-Za-z0-9_-]+)/g) || [];
    for (const cls of clsMatches) {
      if (!el.classList.contains(cls.slice(1))) return false;
    }
    const attrMatches = part.match(/\[([^=\]]+)(?:=\"([^\"]*)\")?\]/g) || [];
    for (const attrMatch of attrMatches) {
      const [, name, expected] = attrMatch.match(/\[([^=\]]+)(?:=\"([^\"]*)\")?\]/);
      const value = el.getAttribute(name);
      if (value === null) return false;
      if (expected !== undefined && String(value) !== String(expected)) return false;
    }
    return clsMatches.length > 0 || attrMatches.length > 0;
  });
}
function buildToolRow() {
  const row = new FakeElement('div');
  row.classList.add('transparent-event-row');
  row.setAttribute('data-event-type', 'tool');
  row._tcData = { name: 'terminal', args: { cmd: 'pwd' }, snippet: 'workspace' };
  const card = new FakeElement('div');
  const header = new FakeElement('div');
  header.classList.add('tool-card-header');
  const copy = new FakeElement('span');
  copy.classList.add('transparent-event-copy');
  copy.innerHTML = 'copy-icon';
  header.appendChild(copy);
  card.appendChild(header);
  row.appendChild(card);
  return { row, header, copy };
}
let nextTimerId = 1;
const timers = [];
const activeTimers = new Set();
const clearedTimers = [];
global.setTimeout = (cb, ms) => {
  const id = nextTimerId++;
  timers.push({ id, cb: () => { activeTimers.delete(id); cb(); }, ms });
  activeTimers.add(id);
  return id;
};
global.clearTimeout = (id) => {
  clearedTimers.push(id);
  activeTimers.delete(id);
};
const copied = [];
const toasts = [];
global.li = (name, size) => `icon:${name}:${size}`;
global.t = (key) => key === 'copied' ? 'Copied' : key === 'copy' ? 'Copy' : key;
global.showToast = (message, duration, kind) => toasts.push({ message, duration, kind });
eval(extractFunc('_copyEventToClipboard'));
eval(extractFunc('_attachCopyButton'));
"""


@pytest.mark.skipif(NODE is None, reason="node not on PATH")
def test_transparent_event_copy_button_enters_copied_tick_state_after_clipboard_success():
    data = _run_node_script(
        NODE_DRIVER_PREFIX
        + r"""
Object.defineProperty(global, 'navigator', {
  configurable: true,
  value: { clipboard: { writeText(text) { copied.push(text); return { then(fn) { fn(); return { catch() {} }; } }; } } },
});
global.document = { createElement: tag => new FakeElement(tag), body: new FakeElement('body'), execCommand: () => true };
const { header, copy } = buildToolRow();
_attachCopyButton(header);
copy.onclick({ stopPropagation() {}, preventDefault() {} });
process.stdout.write(JSON.stringify({
  copiedText: copied[0],
  buttonHtml: copy.innerHTML,
  buttonColor: copy.style.color,
  timerMs: timers[0] && timers[0].ms,
  toast: toasts[0],
}));
"""
    )

    assert "tool: terminal" in data["copiedText"]
    assert '"cmd": "pwd"' in data["copiedText"]
    assert "workspace" in data["copiedText"]
    assert data["buttonHtml"] == "icon:check:11"
    assert data["buttonColor"] == "var(--blue)"
    assert data["timerMs"] == 1500
    assert data["toast"]["message"] == "Copied tool terminal"


@pytest.mark.skipif(NODE is None, reason="node not on PATH")
def test_transparent_event_copy_button_feedback_resets_after_timeout():
    data = _run_node_script(
        NODE_DRIVER_PREFIX
        + r"""
Object.defineProperty(global, 'navigator', {
  configurable: true,
  value: { clipboard: { writeText(text) { copied.push(text); return { then(fn) { fn(); return { catch() {} }; } }; } } },
});
global.document = { createElement: tag => new FakeElement(tag), body: new FakeElement('body'), execCommand: () => true };
const { header, copy } = buildToolRow();
_attachCopyButton(header);
copy.onclick({ stopPropagation() {}, preventDefault() {} });
timers[0].cb();
process.stdout.write(JSON.stringify({
  buttonHtml: copy.innerHTML,
  buttonColor: copy.style.color || '',
  originalCleared: copy._transparentCopyOriginalHtml === undefined,
  resetTimer: copy._transparentCopyResetTimer,
}));
"""
    )

    assert data["buttonHtml"] == "copy-icon"
    assert data["buttonColor"] == ""
    assert data["originalCleared"] is True
    assert data["resetTimer"] is None


@pytest.mark.skipif(NODE is None, reason="node not on PATH")
def test_transparent_event_copy_button_repeated_clicks_replace_pending_timer():
    data = _run_node_script(
        NODE_DRIVER_PREFIX
        + r"""
Object.defineProperty(global, 'navigator', {
  configurable: true,
  value: { clipboard: { writeText(text) { copied.push(text); return { then(fn) { fn(); return { catch() {} }; } }; } } },
});
global.document = { createElement: tag => new FakeElement(tag), body: new FakeElement('body'), execCommand: () => true };
const { header, copy } = buildToolRow();
_attachCopyButton(header);
copy.onclick({ stopPropagation() {}, preventDefault() {} });
const firstTimer = copy._transparentCopyResetTimer;
copy.onclick({ stopPropagation() {}, preventDefault() {} });
const secondTimer = copy._transparentCopyResetTimer;
timers.find(timer => timer.id === secondTimer).cb();
process.stdout.write(JSON.stringify({
  copiedCount: copied.length,
  firstTimer,
  secondTimer,
  clearedTimers,
  activeTimerCount: activeTimers.size,
  buttonHtml: copy.innerHTML,
  buttonColor: copy.style.color || '',
}));
"""
    )

    assert data["copiedCount"] == 2
    assert data["firstTimer"] != data["secondTimer"]
    assert data["clearedTimers"] == [data["firstTimer"]]
    assert data["activeTimerCount"] == 0
    assert data["buttonHtml"] == "copy-icon"
    assert data["buttonColor"] == ""


@pytest.mark.skipif(NODE is None, reason="node not on PATH")
def test_transparent_event_copy_button_fallback_success_enters_copied_tick_state():
    data = _run_node_script(
        NODE_DRIVER_PREFIX
        + r"""
Object.defineProperty(global, 'navigator', { configurable: true, value: {} });
let appendedTextarea = null;
global.document = {
  createElement(tag) {
    const node = new FakeElement(tag);
    node.select = () => {};
    return node;
  },
  body: {
    appendChild(node) { appendedTextarea = node; },
    removeChild(node) { if (node !== appendedTextarea) throw new Error('wrong textarea removed'); appendedTextarea = null; },
  },
  execCommand(command) {
    copied.push({ command, value: appendedTextarea && appendedTextarea.value });
    return true;
  },
};
const { header, copy } = buildToolRow();
_attachCopyButton(header);
copy.onclick({ stopPropagation() {}, preventDefault() {} });
process.stdout.write(JSON.stringify({
  copiedCommand: copied[0] && copied[0].command,
  copiedText: copied[0] && copied[0].value,
  buttonHtml: copy.innerHTML,
  buttonColor: copy.style.color,
  toast: toasts[0],
}));
"""
    )

    assert data["copiedCommand"] == "copy"
    assert "tool: terminal" in data["copiedText"]
    assert data["buttonHtml"] == "icon:check:11"
    assert data["buttonColor"] == "var(--blue)"
    assert data["toast"]["message"] == "Copied"
