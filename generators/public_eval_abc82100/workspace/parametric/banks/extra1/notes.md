# Current authoring state

Reviewer-ready unapproved public family for `abc82100`; owner registration,
source reconciliation, native qualification and acceptance remain required.
No shared canonical authority or immutable parent provenance was changed.

## Rule and parameter

A source-color pixel and a distinct output-color pixel form an oriented pointer.
The first occupied cell along its forward ray must be cyan (8). Recover that
cyan 8-component and its offsets relative to the cell one step beyond the
output-color marker. The entry cell can be empty; using the stencil bounding-box
corner would be wrong. Remove all cyan and all pointer pixels, clear the remaining
source seeds, and stamp the recovered shape at every corresponding seed in the
pointer's output color. Unmapped colors remain. Stamps clip at the canvas edge.
The two supplied test answers are both reproduced, including touching stencils.

When several pointers enter one touching cyan component, forward-facing cells
are assigned to the nearest pointer axis, then nearest anchor, then row-major
pointer on ties. This is an authored generalization supported by the provided
examples, not a claim that finite examples uniquely determine behavior on every
possible overlapping diagram. Generated scenes use two adjacent oppositely
oriented bars to exercise the actual touching case; same-cell paint collisions
use deterministic pointer order. No official grid or answer is read by generation.

`stencil_action=as_drawn` uses the exact reference bytes copied to canonical.rkt.
`quarter_turn` rotates recovered signed offsets clockwise about the entry anchor
before stamping. Input streams remain matched, including all four query inputs.
The variant does not replace stencil inference with an unrelated task.

## Sampler and privacy

2–6 demonstrations and independent 1–4 query prefixes. Every request retains a
private bank of exactly four queries; query four is 30×30 with long touching
stencils, additional templates, many seeds and boundary clipping. Keyed GenCtx
streams isolate seed/sample-index randomness. All seeds and settings are private.
Single-turn projection shuffles the entire bank with an independent presentation
seed before selecting a turn, selects only train input/output and current test
input, and never emits a turn counter, total count, settings, programs, answers
or future queries. Public IDs are hashes of exact visible bytes. Never expose
its controller-side public-file directory listing.

## Executed evidence and bounds

Six original labels (four demos and two test gold) matched protected Racket.
17 focused tests passed. Authoring preflight passed both settings, seeds 17/43,
two demonstrations and four queries. The reusable audit tested 64 seeds, both
settings and all five supported demonstration prefixes: 640 lesson views and
5,120 pair exposures, representing 640 distinct input draws rather than 5,120
independent draws. Eleven finite rivals had zero query-changing survivors.
Extra max-demo labels and a separate causal replay passed (24 protected
executions). Public projection produced 16 content-hashed single-query views.
The source-bound witness replaces the recovered offset table with singleton
zero offsets, changing 81 cells of the retained 30×30 quarter-turn output.

The initial stress construction's occupancy floor was impossible for short
bars; a regression caught it. The 30×30 branch now samples 12–15-cell bars.
Early failing tests and the successful reruns are retained in WORK/checks.
Final audit and review were author-performed; no independent reviewer was used.
The finite rivals/seeds do not establish universal identifiability, universal
source-rule intent, measured learning benefit, or training admission.

## Reproduce

From the packet root, use `review.py run python3 -m pytest
generators/public_eval_abc82100/tests --import-mode=importlib -q`, then the
public-creation preflight command in DUTIES.md. Run the task-local
`workspace/parametric/audit.py --preflight PATH --out NEW_PATH --seeds 64`.
The audit rejects source drift and existing evidence directories.

Return-contract regression: the native witness intake requires an exact minimal
`racket` marker; full runtime attestation is now retained as `runtime_identity`.
A serializer regression failed first, then passed against the unchanged native
validator. Both preflight and all audit evidence were regenerated after the fix.
