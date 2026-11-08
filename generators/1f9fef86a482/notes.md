# Working notes: 1f9fef86a482

## Selected repair (v3.0.0)

The v2.0.1 sampler produced separated star motifs whose maximum graph degree was
always the blue-header count.  Across a deterministic 600-instance probe, the
wrong rule “paint all maximum-degree components” matched the canonical authority
600/600 times and no generated scene contained a degree above the requested
one (`checks/baseline-shortcut-probe/finding.json`).

The repair narrows the public controls to four pixel-observable axes and widens
the semantic curriculum instead:

- canonical-linked chain and degree-3 star anchors;
- an `all_degrees` graph with degrees 0 through 4, repeated colours, and an
  explicit degree-above-target distractor;
- a four-slot deterministic schedule that keeps every three-example lesson and
  every cyclic three-of-four subset identifiable against declared rivals;
- executable semantic witnesses/rivals and a grammar-recognizing `self_check`;
- independent Python analysis/oracle and cyclic lesson probes in `workspace/`;
- task-local regressions in `tests/test_generator.py`.

The canonical Racket authority and canonical puzzle row were not changed.
Remaining limits are deliberate and documented: target counts are 2 or 3, graph
morphologies are finite, and declared-rival identifiability is not a proof
against every possible shortcut.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `fa02b244487ff210c82c374b2274cb0226eedc0733315c8cbab6e4f837843496`.

# Decisions for `1f9fef86a482`

## D1 — Keep the canonical Racket authority unchanged

**Decision.** Treat the retained Racket program and canonical puzzle row as the
label authority, pin its current hash (`dfe6e5f597b6`), and change only the
Python generator, task-local tests, notes, and workspace probes.

**Why.** Independent analysis matched all three canonical pairs, and the defect
was in what the sampler taught—not in the transformation.  Changing the rule
would have widened review scope and invalidated existing labels without evidence.
The final authority-sync stage and Racket execution parity passed.

**Rejected alternative.** Rewrite or simplify the Racket rule to mirror Python.
That would substitute a new authority for a working one and make parity harder
to establish.

**Evidence/limit.** `checks/after-final/checks/1f9fef86a482_after_authority_sync.json`.
An archival bank copy is already divergent, but the selected execution source is
synchronized and was not modified here.

## D2 — Remove pseudo-axes instead of cosmetically wiring them

**Decision.** Replace the broad v2.0.1 surface with four literal, pixel-observable
axes: grid height, grid width, scene profile, and header style.

**Why.** The old `texture`/palette controls were dead, overlapped negative
fixtures, and encouraged a contract that the pixels did not honor.  Exposing
only exact controls makes failures local and lets `observe_overrides` recover the
request from the generated grid.

**Rejected alternatives.** (a) Keep palette aliases and merely vary body colors;
this adds low-value combinatorics while retaining ambiguous ownership.  (b) Keep
`target_degree` as a free override; arbitrary target/profile combinations would
require a much larger graph grammar or structured incompatibility rejections.

**Evidence/limit.** The final override contract accepted 14,220/14,220 draws.
The intentional cost is that target degree is a scheduled curriculum property,
not an externally steerable axis.

## D3 — Preserve canonical-linked anchors

**Decision.** Include a multi-cell chain profile for `k=2` and a multi-cell star
profile for `k=3`, with sizes/degrees matching canonical structural signatures.

**Why.** A generator should not only produce lawful labels; it should retain
substantial support near the original task.  These profiles give recognizable
anchors while varying placement, palette, dimensions, and header positions.

**Rejected alternative.** Use only newly invented singleton graphs.  That would
maximize combinatorial control but risk drifting away from the canonical visual
language.

**Evidence/limit.** The profile-floor gate measured 46/60 exact-profile support
and accepted 3/3 canonical inputs.  The remaining samples are deliberate
counterexample profiles rather than canonical-like anchors.

## D4 — Add an all-degrees counterexample profile

**Decision.** Build a compact graph containing exact degrees 0, 1, 2, 3, and 4,
using nine singleton components and repeated colors, then choose target 2 or 3
from the schedule.

**Why.** This is the smallest robust way found to place a degree above the target
while preserving target matches and several near misses.  It simultaneously
refutes maximum-degree, fixed-degree, color, size, and one-color-one-object
shortcuts.

**Rejected alternatives.** (a) Add only a `k-1` near-miss star: it does not refute
maximum-degree.  (b) Add a second larger star: placement becomes fragile and the
scene still advertises “choose a hub.”  (c) Random graph synthesis: wider but
less auditable, harder to guarantee planar pixel embedding, and unnecessary for
this repair.

**Evidence/limit.** The baseline shortcut probe found 0/600 higher-degree
witnesses; final found 300/600.  The profile is finite and does not cover every
contact graph.

## D5 — Use a four-slot schedule with deletion-robust lessons

**Decision.** Schedule `chain_k2`, `all_degrees_k2`, `star_k3`,
`all_degrees_k3`, and alternate header styles independently.

**Why.** A three-profile schedule made ordinary sliding windows identifiable but
failed when the wrong profile became the query.  The four-slot schedule is the
smallest pattern in which every three-of-four subset retains both a target-3
example and a higher-degree distractor.

**Rejected alternatives.** (a) Rely on random frequency; aggregate witness counts
do not guarantee each assembled lesson contains a witness.  (b) Test only the
canonical train/query arrangement; production may rotate or reassemble pairs.
(c) Duplicate every profile at both targets in a six- or eight-slot cycle; robust
but unnecessarily lengthens the curriculum period.

**Evidence/limit.** `checks/task-local-cyclic-lesson-probe.json` covers 1,200
rotations with zero ambiguity.  Blocks larger than four and nonconsecutive custom
assembly remain outside this proof.

## D6 — Make semantic claims executable

**Decision.** Declare witnesses, rivals, canonical shortcuts, semantic signatures,
a mirror, and lesson-identifiability hook as callables over actual grids.

**Why.** Prose like “near miss” is easy to satisfy vacuously.  Executable claims
allow the shared semantic gate and future reviewers to verify frequency,
disagreement, canonical fit, and lesson-level refutation against the exact source.

**Rejected alternative.** Keep a bespoke report script only.  That would hide
the intended contract from shared tooling and let declarations drift from code.

**Evidence/limit.** Final semantic gate reports 3/3 witnesses firing, 3/3 rival
claims verified, and 12/12 lessons identifiable.  Declared rivals are not an
exhaustive hypothesis class.

## D7 — Strengthen `self_check` to recognize the grammar

**Decision.** Validate header semantics, separator row, color range, body
components, real cross-component contact, and existence of an exact-degree
answer, rather than merely checking “some nonzero body cell exists.”

**Why.** The old validator accepted solid and one-color impostors and lawful
negative fixtures through the ordinary training path.  A validator should reject
broken generator outputs before they reach Racket labeling.

**Rejected alternative.** Compare against a list of the three known profiles.
That would couple validation to the current sampler and reject lawful canonical
or future graph embeddings.

**Evidence/limit.** 60/60 defaults and 3/3 canonical inputs accepted; 57/60
material destructive mutations rejected.  Three absent-color operations were
no-ops because the selected color did not occur.

## D8 — Use an independent Python oracle only as secondary evidence

**Decision.** Implement flood fill and contact-graph construction independently
in `reference_probe.py`, but retain Racket as authority.

**Why.** Independent code catches generator/mirror coupling and makes fast
regression tests possible.  Calling generator-private helpers would only test the
same implementation twice.

**Rejected alternative.** Import the Racket runner into every unit test.  That is
slower, brittle in local layouts, and unnecessary for structural tests after
parity is established by the battery.

**Evidence/limit.** The independent oracle matches every canonical pair and all
generated outputs exercised by task tests.  Common conceptual mistakes could
still exist in both implementations; authority execution remains the final check.

## D9 — Keep deterministic schedule, randomize presentation

**Decision.** Tie lesson-critical profile/target coverage to sample index, while
using seeded randomness for dimensions, translations, colors, and header
positions.

**Why.** Deterministic coverage prevents unlucky lesson windows; presentation
variation prevents pixel memorization and preserves reproducibility.

**Rejected alternative.** Fully random profile choice.  Even a balanced marginal
distribution can assemble an ambiguous lesson.

**Evidence/limit.** The diversity gate reports 100% unique inputs across 300
pairs.  Only 36% of output masks are unique, because graph-equivalent scenes
produce repeated masks; this is a documented semantic rather than input-collapse
limitation.

## D10 — Build reusable probes and tests, not just a one-off fix

**Decision.** Retain 34 task-local regressions plus source-bound baseline and
cyclic lesson probes.

**Why.** The most important failures occur at distribution and lesson assembly
levels, which ordinary single-instance tests do not cover.  Future edits can now
compare another source via `GENERATOR_UNDER_TEST` and import the source's actual
rival declarations.

**Rejected alternative.** Record only screenshots/examples in review prose.
Those are hard to replay and do not bind to generator bytes.

**Evidence/limit.** Focused tests pass 34/34; the fresh-packet patch replay also
passes 34/34 and matches the checked generator hash (`checks/fresh-replay/result.json`).  The probes intentionally do not claim universal induction.

## Parametric native handoff — review-43359e508d5bcb7f (2026-10-24)

Selected one episode-fixed parameter, `header_measure`, with settings
`blue_cells` (the exact canonical default) and `blue_runs` (count contiguous
blue runs in row 0). Inputs are matched across settings. The two-example lesson
contains one agreement case followed by one separating case; the four stored
queries are prefix-stable, and query four is a substantive 30x30 graph containing
degrees 0 through 4.

Sequential dependency: A scans row 0 and decodes the target graph degree;
the intermediate is that input-derived integer; B constructs the body contact
graph and paints exactly components of that degree. The protected-Racket witness
uses the 30x30 `blue_runs` query: the correct intermediate 2 paints twenty arm
components, while substituting the blue-cell intermediate 4 paints five hubs.

The finite self-audit tested nine declared shortcuts over 256 episodes and found
no rival that fit all visible demonstrations while changing a query. Native
qualification passed for both settings at two demos and again at six demos.
Canonical Racket bytes and production `generator.py` remain unchanged. The next
action is owner integration followed by fresh native qualification/acceptance;
this reviewer return does not admit training data.
