# Working notes: 7bba59d92716

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `6d536e11b6e7c445af3c0b771a73acb8ea94b3aae265761dea87fce1ed8be313`.

# Design decisions — 7bba59d92716

## D1. Keep the selected Racket authority unchanged

**Original rationale:** unknown beyond the canonical rule text.
**Decision:** retain rule hash `0f19aed9b60e`; repair generation and teaching rather than alter output semantics.
**Alternatives considered:** rewrite the rule to match the baseline run-oriented distribution; rejected because canonical outputs and the exact branch witness confirm component-aware semantics.
**Probe:** `checks/root-cause/branch-witness/racket.json`.
**Failure mode/limit:** Racket confirmation covers exact inputs; the Python mirror remains reviewer tooling, not authority.

## D2. Replace generic dimensions with exact canonical profiles

**Original choice/rationale:** baseline sampled generic `grid_h`/`grid_w`; rationale unknown. It did not pin `RULE_HASH` and did not match every canonical shape/palette profile.
**Decision:** schedule the five observed canonical profiles `(8×10,4 colors)`, `(8×13,3)`, `(9×12,4)`, `(10×11,3)`, `(10×13,3)`.
**Alternatives:** one broad independent height/width/palette range; rejected because many combinations had no canonical support and exact overrides became difficult to validate. Canonical profiles only with no variation; rejected because each profile can still support layout, target-count, decoy, and distractor variation.
**Probe:** canonical parsing and profile extraction in `workspace/reference_probe.py`; profile-floor and distribution stages.
**Limit:** this intentionally restricts ordinary training to the canonical profile manifold.

## D3. Use four observable public controls

**Original choice/rationale:** nine scaffold-like axes were advertised, but several were aliases, constants, ignored, or overlapped degenerate textures; rationale unknown.
**Decision:** expose only `profile`, `n_targets`, `decoy_length`, and `n_distractors`. Validate names/types/domains before generation and recover all four from pixels with `observe_overrides`.
**Alternatives:** preserve compatibility aliases; rejected because silent aliases preserve the exact defect. Expose every latent placement choice; rejected as unnecessary and brittle.
**Probe:** exact override matrix in task tests and the shared override stage.
**Failure mode/limit:** branch pattern and placement remain deterministic latent variation, not caller controls.

## D4. Vary target count between two and three

**Original choice/rationale:** baseline hard-coded two targets, apparently for simple placement; canonical labeled pairs contain three.
**Decision:** schedule two and three targets and support exact overrides for both.
**Alternatives:** always three to mimic canonical counts; rejected because two gives lawful variation while retaining at least two positive examples. One or four; rejected for weaker teaching or width pressure in the smallest profile.
**Probe:** generated axis observation over 30 draws/band and exact override tests.
**Failure mode/limit:** target-count variation is small by design.

## D5. Put a branched five-run in every ordinary input

**Original choice/rationale:** baseline explicitly separated all vertical lines to prevent accidental component merging; that made labels valid but erased the distinction between a run and a component.
**Decision:** construct one deliberate same-color branched component alongside isolated targets. The branch spine is an extreme selected column and arms point outward, preventing accidental mergers.
**Alternatives:** occasional branch witnesses; rejected because some lessons could omit the decisive negative. Random unvalidated noise; rejected because it can create unintended components.
**Probe:** initial exact witness, `run5_ignores_branches`, shared semantic gate, reference probe.
**Failure mode/limit:** finite branch families do not enumerate every possible connected shape.

## D6. Vary branch attachment rows and component size

**Original repair choice/rationale:** the first repair attached one arm at the midpoint because it was simple and visibly branched.
**Observed failure:** a narrower rule—“mark a five-run unless its midpoint has a side neighbor”—fit all canonical pairs and all 120 sampled 2.0.0 defaults. A second rival could exempt only six-cell branches. `checks/new-shortcut/probe-before.json` records zero counterexamples for both.
**Decision:** cycle patterns `(0)`, `(1,3)`, `(4)`, `(0,4)` relative to the five-run, alternating branch-component sizes 6 and 7. All arms are off midpoint.
**Alternatives:** document the hole only; rejected. Random arm rows; rejected because arbitrary three-demo windows could lack size variation. One fixed off-midpoint arm; rejected because it simply moves the positional shortcut.
**Probe:** failing-then-passing regression, exact top-branch Racket witness, 40 draws/band, all cyclic four-pair starts.
**Failure mode/limit:** other shape-specific hypotheses remain possible outside the scheduled family.

## D7. Include a horizontal five-cell component in every ordinary input

**Original choice/rationale:** baseline provided no same-size nonvertical component.
**Decision:** place a horizontal color-1 line of length five at the top or bottom with a blank buffer row.
**Alternative:** irregular five-cell blobs; useful, but the horizontal line is the cleanest direct test of orientation and easier to place constructively.
**Probe:** `component_size5_any_shape` and `all_vertical_components` rivals.
**Failure mode/limit:** horizontal position is edge-biased to simplify collision-free packing.

## D8. Schedule wrong-length vertical decoys as `6,3,6,4`

**Original choice/rationale:** baseline used one length-2/3 short decoy; no long negative appeared in ordinary draws.
**First repair:** a `3,4,6` cycle.
**Observed failure:** in a four-pair lesson, holding out the only length-6 pair left three demonstrations compatible with “length at least five”; retained at `checks/semantic-smoke-v2.json`.
**Decision:** use `6,3,6,4`. Every four consecutive pairs contain two length-6 negatives, so every held-out-query rotation leaves at least one in the demonstrations.
**Alternatives:** length 6 in every pair; rejected as less varied. Resample ambiguous lessons; rejected in favor of a transparent deterministic schedule.
**Probe:** exhaustive starts 0–7 in every band and 1,200 census rotations.
**Limit:** the schedule is designed around four-pair lessons with three demonstrations and one query.

## D9. Keep 2–4 accent distractors and exact palette profiles

**Original choice/rationale:** baseline placed one color-6 marker; rationale unknown.
**Decision:** place 2–4 color-6/7 cells. Three-color profiles use one accent color; four-color profiles guarantee both.
**Alternatives:** arbitrary ARC colors; rejected because canonical input colors are 0/1/6/7. No distractors; rejected because it would narrow the visual distribution.
**Probe:** profile observer, canonical-profile tests, distribution gate.
**Failure mode/limit:** accent-cell geometry is not semantically meaningful and is not a public axis.

## D10. Construct layouts instead of retrying random placements

**Original choice/rationale:** baseline used spaced columns and a deterministic fallback after random attempts.
**Decision:** enumerate legal separated column sets, choose a valid extreme branch column, reserve a buffered horizontal edge row, and paint objects with collision assertions.
**Alternatives:** broad rejection sampling; rejected for hidden support bias and occasional failure.
**Probe:** deterministic/fresh-output tests, self-check across shared battery draws, 1,200 unique census inputs.
**Failure mode/limit:** the constructive grammar is deliberately narrower than all `self_check`-accepted inputs.

## D11. Make the lesson contract executable

**Original choice/rationale:** no semantic contract; shared check reported `NO_CONTRACT`.
**Decision:** declare `rule_mirror`, witnesses, canonical shortcuts, six competitors, `EXAMPLES_NEEDED=3`, and `lesson_identifiable`. Bundle rivals sharing one witness to reduce authority calls, while keeping individual positive branch predicates.
**Alternatives:** rely only on correct per-grid labels; rejected because correct labels can still form ambiguous lessons.
**Probe:** strict semantic gate, all cyclic task-local rotations, 100 lessons/band census.
**Limit:** finite declared rivals do not establish unique induction over an unrestricted hypothesis class.

## D12. Add independent, portable task-local reviewer tooling

**Original choice/rationale:** no selected-task tests or reusable semantic probe.
**Decision:** add 35 tests and `workspace/reference_probe.py`; load canonical data with `reviewer_support.find_root`/`canonical_pairs`, and keep rival implementations independent of generator internals.
**Alternatives:** inspect grids manually; rejected as irreproducible. Copy Racket/private runner helpers; rejected because supported public APIs already provide authority evidence.
**Probe:** source-bound `task_tests` stage and exact fresh-copy patch replay at `checks/final-handoff/replay.json`.
**Limit:** Python mirrors are diagnostics; final truth remains the selected Racket rule.

## Lesson assembly policy

The intended export unit is four consecutive labeled pairs: three demonstrations and one query. Production uses the sampler's selected query; rotation verification holds out each pair once and preserves the order of the remaining three. The deterministic decoy and branch schedules were checked over every cyclic start used by the small schedule tests and over 100 starts per band in the source-bound census.


## Current opt-in marker-size parametric family

`workspace/parametric/` adds `length_rule=fixed_five|marker_size`; production
source and the exact canonical rule remain unchanged. The default returns the
canonical Racket string verbatim. The alternative counts the unique color-6
component, then uses that input-dependent number to select exact vertical blue
4-components before marking their middle cells. This is contextual gating, not
iterative grid simulation. The computed count is essential: substituting five
changes which blue objects receive a red middle. Native causal replay records
that intervention on qualified three- and seven-cell marker examples.

The retained sampler supports 2–6 demonstrations (default three) and 1–4 queries
independently. First-two markers have sizes three and seven; matching inputs
across settings prevent private setting-dependent geometry. Separate per-split,
per-index RNG streams preserve prefixes. It constructs true targets plus
branched, horizontal, wrong-length and diagonal-contact negatives, with a
unique nonrectangular marker and a color-7 distractor. Reflections preserve
vertical orientation. Four queries include 30×30 with actual component content
across every quadrant; dimensions and geometry are in the workspace README.

A bounded independent audit checks the other setting and seven explicit rivals:
run-only, any-shape, all-odd-vertical, eight-connectivity, marker bbox area, marker height and boundary-cell count. In particular, diagonal contacts repair a prototype teaching
hole inherited from the production layout's separated objects. The old
production support does not teach that connectivity distinction; this prototype
work does not change the production generator or claim historical audit closure.
The two original audit rows therefore retain their existing needs_triage status.

The initial seven-cell H marker left a two-demo boundary-count shortcut: every
cell was a boundary cell, so the rival matched both demos but selected length
four instead of five on the later cross-marker query. Six protected Racket
executions retained in `boundary-before-racket.json` confirm that original hole.
The marker now uses a cross plus two opposite corners: its interior center
makes total size seven differ from boundary size six in the second demo. This
repairs the hole without increasing demo count; the regression failed before
the change and passes afterward.

Current evidence: `workspace/parametric/evidence/current/audit.json` records
80/80 sampler requests, eight lessons, 368 successful protected Racket executions,
64 checked chosen labels, thirteen decisive demo witnesses, no observed
demonstration-fitting rival with a different query answer, and unchanged source
during the audit. `task-tests-summary.json` records 88 passing isolated task
tests. These are finite checks, not universal identification or domain proofs.

`audit.py` and `rivals.py` are runnable independent audit tools.
`export_qualified.py` reuses native current-source/receipt validation and emits
one-query public views with visible-byte hash names; all order, settings,
seeds, programs and answers remain private. It verifies serialization and does
not replay Racket or implement a turn controller. Owner integration, fresh
qualification and exact-source native acceptance remain the next admission
steps. No training activation is included.
