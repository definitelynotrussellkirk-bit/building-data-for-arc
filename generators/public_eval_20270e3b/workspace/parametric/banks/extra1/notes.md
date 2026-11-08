# Public parent 20270e3b — authoring design

Blue is background. Two 8-connected yellow/orange pieces have orange mating
ports. Translate one piece without rotation until both pieces' orange ports
are covered by the other's yellow cells, with no yellow/yellow collision.
Erase the ports and crop the joined yellow assembly. This is a geometric
alignment rule, not concatenation of bounding boxes or overlay of the ports.
Verify the hypothesis on four train labels and both private test gold labels.

The default reference is canonical assembly. The alternative `enclosed_fill_relay`
fills blue pockets that are 4-connectedly enclosed AFTER assembly with cyan 8.
A produces the assembled boundary; B floods its complement. Filling the two
separate pieces before joining fails on pockets closed only by joining. The
sampler must include unequal bounding boxes, offset ports, 8-connected diagonal
parts, old and newly formed holes, and exterior blue within the output crop.

Plan:
- [x] Pin original labels, boundary, adversarial and privacy invariants in tests.
- [x] Implement independent Python/Racket geometric docking and fresh sampler.
- [x] Add post-assembly filling, a pre-assembly counterfactual and native adapter.
- [x] Repair demonstrated ambiguities; audit finite rival families.
- [x] Protected-Racket preflight, public exports and source-bound causal replay.

Review focus: both ports matter; yellow overlap is forbidden; figures use
8-connectivity while enclosed backgrounds use 4-connectivity; assembly can grow
one output dimension while shrinking another; crop must retain external blue;
source pieces and query order must not encode the setting. No official grids
or gold labels may be looked up by production source.

This is unapproved authoring work. Owner registration/qualification/acceptance
and training admission are separate and pending.

## Current rule refinements and evidence

Mutual coverage alone was insufficient: it admitted sideways slips on official
train 0 and both official test inputs. The full orange patterns must be identical
up to a unit cardinal displacement after docking. That geometric constraint now
matches every official label. A named `loose_port_overlap` rival retains the
rejected hypothesis; the first generated demo deliberately exposes it.

Boundary self-review found a Python/Racket mismatch on two L-shaped pieces:
one apparent docking was 31 columns wide, while another was a valid 30-column
assembly. All Racket programs now filter candidates by the same 30×30 output
limit as Python. A protected-Racket regression exercises both settings on this
non-sampler edge case. The failing-before and passing-after logs are retained.

Current checks: 81 task tests pass; four original demonstrations plus both
private test golds match protected Racket. The 64-seed, 2-mode, 2/3/6-demo audit
covers 384 episodes and 3,840 named-rival checks without a retained failure.
It performs 82 protected-Racket evaluations plus a fresh two-program replay.
The 30×30 witness has 224 newly enclosed cells missed by the pre-assembly fill.
All 16 one-query public exports pass identity/schema checks. Twenty hidden-field
mutations preserve visible bytes; six malformed-export cases are rejected.

Rerun `workspace/parametric/verify.py --preflight PATH --out NEW --seeds 64`
with the checkout runtime. The tool refuses stale source bindings, audits declared
rivals, exports independent public views, and constructs/replays the causal case.
The checks are finite, not a universal uniqueness proof. Final review is an author
self-review; no independent reviewer was available. Owner registration, native
qualification/acceptance, and any training admission remain pending.
