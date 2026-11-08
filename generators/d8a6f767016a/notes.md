# Working notes: d8a6f767016a

## Review outcome — 2026-10-07

The imported v3 generator preserved the canonical rule, but its public contract
and teaching distribution were not acceptance-ready. The before battery was
`6 green / 2 advisory / 4 failed`: lint could not observe `n_objects`, defect
lint rejected undeclared degenerate textures, mixed overrides were inert and an
unknown key was accepted, and the selected Racket authority representations
were not synchronized. Evidence:
`checks/before/checks/d8a6f767016a_before_battery_summary.json`.

The strongest plausible canonical-training shortcut was component size rather
than topology. Across all four training demonstrations, object sizes separate
perfectly into `8..12→1`, `13..17→3`, `18..25→2`, and `26+→4`. It fits all four
training pairs but fails the labelled canonical test pair. The retained exact
counterexample has two one-hole rings with 14 and 8 cells; the intended Racket
rule colors both 1, while the rival colors the 14-cell ring 3. Evidence:
`workspace/shortcut_probe.py`, `checks/shortcut-counterexample-input.json`,
`checks/shortcut-counterexample-racket.json`, and
`checks/shortcut-probe-report.json`.

Version 4 replaces best-effort and degenerate controls with two exact dimension
axes, adds a strict validator and observable override hook, and uses a
constructive backtracking packer. Every ordinary draw includes a 14-cell
one-hole witness, while the four-sample schedule covers counts 2, 3, 4, and the
0-hole else branch. Shape orientations are chosen jointly with the canvas; this
fixes the minimized `9x11`, count-4 placement failure at seed 27/sample 462.

The Python rule mirror and semantic rival are diagnostics only. Canonical Racket
remains label authority. The selected base record's `racket_target.target_code`
was reformatted to exactly match the canonical `program_solution`; the rule
hash and behavior did not change. The archival `raw_code` remains divergent and
is explicitly reported by the authority-sync gate. A pre-change copy is kept at
`workspace/authority-before.json`.

Final generator SHA-256:
`c9431e2a1c362bb895cfb66f51e4625033cb972fc3326b226aaddd456ab73ff0`.
The after battery is 12/12 green, task tests are 9/9, the strict semantic census
is 600/600, and the 300-lesson census reports 0 ambiguities in 300 production
lessons and 0 in 1,500 query rotations against the declared rival. These are
finite declared-rival checks, not a proof of unique induction against every
possible hypothesis.

The July associated note is retained as historical evidence in
`evidence/associated_notes.jsonl`. It was used only as a stale lead; every final
claim above was re-measured against the packet's frozen baseline and final
source.
## Current reviewer considerations

Source SHA-256: `c9431e2a1c362bb895cfb66f51e4625033cb972fc3326b226aaddd456ab73ff0`.

# Decisions: d8a6f767016a

## D1 — Preserve the canonical topology rule

**Decision.** Keep `RULE_HASH=feb6e892870b` and the transformation “count the
enclosed zero-regions in each color-8 object's own bounding box; recolor by
1→1, 2→3, 3→2, 4→4, otherwise keep 8.”

**Rationale.** Rule smoke, five canonical pairs, and the retained Racket source
agree. The assignment was a generator repair, not a rule redesign.

**Alternatives rejected.** Counting divider strokes, using global background
regions, or mapping component size directly all fit some visible regularities
but disagree with canonical outputs.

**Probe and failure mode.** `rule_mirror` is checked against all five canonical
pairs, while canonical Racket labels the exact counterexample. The Python mirror
is diagnostic and cannot replace Racket authority.

## D2 — Treat component-size bands as the strongest measured rival

**Decision.** Declare and test the rival
`8..12→1, 13..17→3, 18..25→2, 26+→4`.

**Original rationale.** Unknown. The retained July note warned about a different
“divider walls + 1” shortcut, but the current canonical training objects expose
a stronger exact correlation with component size. That historical note was used
only to motivate a fresh search.

**Alternatives considered.** Bounding-box area, width/height, object order,
simple geometric transforms, and the earlier divider-count heuristic. Component
size was preferred because it fits every object in all four training pairs with
a four-line rule and requires no topology.

**Probe.** `workspace/shortcut_probe.py` verifies 4/4 training fit, 0/1 canonical
test fit, and the exact two-ring disagreement. Limitation: it is one named rival,
not an exhaustive hypothesis search.

## D3 — Put a rival counterexample in every ordinary draw

**Decision.** Require a 14-cell one-hole frame in every generated grid.

**Rationale.** Under the intended rule it becomes color 1; under the size rival
it becomes color 3. A per-draw invariant is stronger and easier to audit than a
low-probability mixture.

**Alternatives rejected.** Rare stochastic counterexamples could leave complete
lessons ambiguous. Very large one-hole rings would not fit every advertised
canvas. An 8-cell ring agrees with the rival and therefore teaches nothing about
this shortcut.

**Probe and failure mode.** Task tests check every sampled draw and semantic gate
measures 600/600 witness hits. This only refutes size-bin rules that make the
same prediction as the declared rival.

## D4 — Use a four-profile ordered curriculum

**Decision.** Set `EXAMPLES_NEEDED=4`; cycle sample indices through `count_2`,
`count_3`, `count_4`, and `else_0`, with one query after the four demonstrations.

**Rationale.** Four demonstrations cover every nontrivial output mapping and the
unchanged else branch while each also carries the one-hole counterexample.
Consecutive starts rotate the order rather than privileging one branch.

**Alternatives rejected.** Two or three demonstrations cannot guarantee coverage
of all four scheduled companion branches. Random independent branch draws can
omit rare counts from a lesson. Five or more demonstrations added cost without
refuting the measured rival more strongly.

**Probe and limitations.** Task tests enumerate cyclic starts. The semantic smoke
checks 12 lessons and 60 rotations; the source-bound census checks 300 production
lessons and 1,500 query holdouts. The curriculum is intentionally ordered, even
though all tested holdout rotations also passed against the declared rival.

## D5 — Make shape orientation canvas-aware

**Decision.** Enumerate witness/companion orientations jointly and place them by
backtracking with Chebyshev separation; drop only the optional third object if
necessary.

**Rationale.** Independent orientation choices made the valid `9x11`, count-4
case at seed 27/sample 462 impossible even though another orientation fit.

**Alternatives rejected.** Enlarging the minimum canvas would shrink canonical
profile support. Retrying random orientations without enumeration would make the
exact override contract probabilistic. A fallback grid could silently violate
the requested profile.

**Probe.** The minimized regression is retained as
`test_small_canvas_count4_orientation_regression`; full override battery accepted
7,290 cases with no finding or warning.

## D6 — Advertise only exact controls

**Decision.** Keep only exact `grid_h` and `grid_w` axes; reject unknown keys and
remove best-effort object/hole/texture controls.

**Rationale.** The baseline failed because `n_objects` lacked observable exact
semantics, mixed `max_holes`/texture combinations were inert, and an unknown key
was accepted. Exact controls are safer than documenting several interacting
exceptions.

**Alternatives rejected.** Preserving all old axes with incompatibility tables
would retain a large combinatorial contract and invite silent best-effort
behavior. Keeping degenerate textures as public negative examples conflicted
with the default generator's training purpose.

**Probe.** `observe_overrides` round-trips exact dimensions; override stage is
PASS with unknown-key verdict `rejected`.

## D7 — Tighten `self_check` to the actual production domain

**Decision.** Enforce shape, palette, strict modal background, object count,
minimum size, hole ceiling, and full-zero-ring separation, while accepting all
five canonical inputs.

**Rationale.** A validator should define the lawful domain used by diagnostics,
not merely reject malformed arrays. The previous validator admitted or failed
to explain several degenerate cases.

**Alternatives rejected.** Requiring the mandatory 14-cell witness in
`self_check` would reject canonical inputs and conflate production curriculum
with the semantic task domain. Requiring exact scheduled object counts would
make the optional third object unlawful.

**Probe and limitation.** Canonical acceptance is 5/5 and strict generated rate
is 600/600. The validator cannot certify every input on which the Racket program
happens to return a value; it intentionally describes a narrower reviewed domain.

## D8 — Synchronize selected authority text, not rule semantics

**Decision.** Replace only the selected base record's
`racket_target.target_code` formatting with the exact canonical
`program_solution`; preserve `raw_code` and all canonical rows.

**Rationale.** The baseline authority-sync gate reported selected textual
divergence despite execution parity. Exact selected-source synchronization makes
future drift detectable.

**Alternatives rejected.** Changing canonical code or outputs was unnecessary
and forbidden by the evidence. Rewriting archival `raw_code` would erase useful
provenance.

**Probe.** Authority sync is green with execution parity PASS and explicitly
labels `raw_code` as archival divergent. Rule hash remains unchanged.

## D9 — Keep reusable diagnostics beside the generator

**Decision.** Add task-local tests plus `workspace/shortcut_probe.py` and retain
red-phase and minimized failure evidence.

**Rationale.** Future reviewers need an executable rival, exact counterexample,
and portable canonical access rather than a narrative warning.

**Alternatives rejected.** Embedding all checks in production `generate` would
mix authoring diagnostics with sampling. A one-off notebook would not replay in
the staged runtime.

**Limitations.** The reusable probe covers the measured component-size rival.
Broader automated counterfactual search is proposed as shared-tool feedback in
`FEEDBACK_TO_CODEX.md` rather than smuggled into the allowed task delta.
