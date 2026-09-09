# Live scene ordering and terminal ownership

This note describes the presentation-layer contract for the live scene path.
It supplements [Stable Assistant Turn Anchors](../rfcs/stable-assistant-turn-anchors.md)
and [Live-to-Final Assistant Replies](../rfcs/live-to-final-assistant-replies.md).
It does not change run execution, transcript authority, or server validation.

## Ordering provenance

Journal transport sequences and browser-local producer ordinals are different
ordering domains. The trusted producer context selects `order_domain`; raw event
payloads do not get to select it. Regressions within either domain still mark the
projection uncertain and take the full fail-closed path. Comparing a local ordinal
against the next journal offset must not mark valid delivery uncertain.

Stable identity and duplicate detection remain separate from order validation.
The local producer domain must not replace a real journal event identity or
permit ambiguous identity to take the incremental path. Projected rows retain
`order_domain` for snapshot hydration. That hydration boundary restores local
provenance only for rows without a journal event ID; rows with a journal ID and
legacy rows without provenance retain the transport/fail-closed interpretation.
The normalized-event replay API preserves its already-normalized provenance.

## Semantic and visual ownership

Synchronous producer callbacks ingest prose, reasoning and tool state into the
turn's anchor. Normal frame paints and terminal fade steps only project that
state; they must not upsert semantic prose as a consequence of painting.

The stream closure owns the live scene scheduler, generation, pending terminal
completion, fade timeout/frame, snapshot/persistence timers and registry cleanup.
A valid `done` schedules one generation-bound completion. The completion is
claimed and removed before invocation. A transport close during optional fade
must complete that pending semantic work before disposing the owner.

Once terminal state is claimed, later live producer events cannot compete with
it. Already-dispatched callbacks must check the current generation and, where
applicable, the exact scheduled timer handle. Cancellation alone is not proof
that a callback cannot execute.

Explicit supersession/disposal invalidates the owner and clears the pending
completion. It is not permission for an obsolete owner to finalize a successor.
Page teardown first asks the current owner to complete an already-received
terminal result, then uses the existing detach/reattach handoff. A bfcache
`pageshow` uses canonical session loading when an inflight attachment needs
restoring; it does not revive the disposed owner. Session-switch detachment
retains the existing journal-replay recovery contract.
Each recovery rewire re-registers the exact registry and re-arms its backstop.
Registry removal is conditional on exact registry identity so disposal cannot
remove a replacement owner's entry. Disposal is idempotent.

## Incremental projection

Known-order changes rebuild only dirty rows. Immutable scene snapshots share a
private persistent row index rather than copying every historical row reference
on each paint. Live rendering reads `_activity_rows_view`; this non-enumerable
view is not a public dense array. The public `activity_rows` getter materializes
a normal frozen dense array once, retaining native reflection and JSON semantics.
Persistence/replay use that public boundary. Diagnostic counters distinguish the
private live path from explicit public materialization.
Initial construction still uses the full projection. The renderer also retains
its explicit terminal-row fail-closed branch; terminal settlement is not a
steady-state paint. Genuine identity/order uncertainty continues to rebuild.

## Settled persistence

Both Compact Worklog and Transparent Stream naturally use
`POST /api/session/anchor-scene` after settled scene attachment. The endpoint's
256,000-byte UTF-8 scene limit remains authoritative.

Before sending, the client checks a conservative UTF-8 server-serialization
bound. It includes Python's extra exponent digit for numeric values serialized
by JavaScript with `e-7`, `e-8`, or `e-9`; numeric-looking text is not counted as
a number. A known-oversized scene is not posted or truncated: the full in-memory
semantic scene is retained,
a warning is emitted and the existing toast surface reports that persistence
was skipped. Under-budget scenes retain the normal persistence path. The saved
transcript remains authoritative; skipping this derived scene is not a claim
that the anchor cache was saved.

## Verification surfaces

The `test_issue6391_*` tests exercise mixed ordering, real projection work,
immutable snapshots, producer/paint separation, terminal claims, registry
cleanup, budget handling and dispatched stale callbacks. Browser validation
must additionally use real synthetic SSE lifecycles in both display modes,
observe natural persistence and verify replay/reload and terminal cleanup.
Unit results alone do not establish browser performance or persistence success.
