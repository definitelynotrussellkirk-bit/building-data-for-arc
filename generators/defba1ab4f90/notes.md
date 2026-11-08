# Current notes: defba1ab4f90

## Intended rule

A unique non-corner red `2` marker enters from the top or left edge. In top-entry coordinates the red stream falls until it meets a horizontal length-3 bar, moves along the row immediately before that bar, steps one cell beyond the bar, and resumes falling. Blue `1` sends the stream to its left hand; green `3` sends it to its right hand. Left-entry scenes are the transposed case and therefore flip chirality. Bars that the stream never reaches remain unchanged.

## Decision reversal

The imported v1.3.0 source generated an unrelated sparse 13×13 local-motif gallery and could omit the red entry marker. It failed 8 of 12 baseline battery stages. Version 2.0.0 replaces that sampler rather than preserving its texture axes because those axes did not describe the canonical task.

## Current sampler contract

- Construct the exact stream path first, then place active bars and path-disjoint distractor bars. This makes every advertised override constructive rather than rejection-sampled.
- Exact controls: `orientation` (`top|left`), normalized `flow_length` (19..29), normalized `lane_width` (10..15), active `n_turns` (4..8), and `n_distractors` (0..6).
- The default four-slot schedule uses canonical normalized geometries `(22,12)`, `(19,13)`, and `(29,13)` and includes both orientations in every three-demonstration window.
- Every generated scene contains both active blue and active green events. Distractors are length-3 bars on rows disjoint from the intended path.
- `strict_canonical_like`, semantic witnesses, declared rivals, and `lesson_identifiable` are executable contracts. The finite rivals are color-blind steering and failure to flip chirality after transposition.

## Authority decision

The canonical rule hash remains `c58d2da3a0e5` and the canonical ledger was not edited. A stale augmented selected base-authority file still contained an unrelated local-rewrite program, so both selected task base records were synchronized to the already-canonical stream program and marked as selected authority. This is a selected-source repair, not a change to the intended transformation.

## Final evidence

Generator SHA-256: `4189136b4e863e70bf07ee2466d865493554544a72273e4f3918da61da7f7c26`.

- Aggregate after battery: 12/12 green.
- Task-local tests: 48/48 passed.
- Exact-override matrix: 35,730/35,730 accepted draws, zero findings.
- Strict semantic census: 600/600 generated inputs accepted; both witnesses fired in every band.
- Production lesson census: 300 lessons, 1,200 labeled pairs and 1,200 unique inputs; zero declared-rival ambiguity in production or in 1,200 held-out query rotations.

## Native parametric family: paired handedness

`workspace/parametric/` adds canonical/reversed steering with identical inputs
across settings, 2–6 demos, four independently sampled novel queries, and true
30×30 top/left scenes. Both rules follow 5–12 active color decisions; a guarded
bar grammar keeps every declared alternative total. The canonical default is
byte-identical to the selected rule; production generator/authorities are unchanged.

Current bounded verification: 27 focused tests and 75 final staged task tests
pass. Native qualification ran 12 jobs across two settings, seeds 0/17, and
demonstration counts 2/3/6. The replay tool checked 192 Python census episodes
(maximum two demo-selection attempts), plus 46 protected-Racket executions for
two retained lessons, declared rivals and the causal ablation. Eight one-query
public exports passed the saved-byte/identity checker. None of these finite
checks establishes universal identifiability or owner admission.

The native adapter, promotion contract, inventory, portable tests and reusable
`verify.py` are retained together. Demonstrations distinguish both settings and
four explicit shortcut rules. The causal witness makes the next reached bar's
color necessary for the next slide, not a cosmetic remap. Exact-source owner
acceptance remains downstream; no training data are admitted here.

The existing `review-a70ce13a9b78aaa3:v0001` scalar-call audit remains unresolved
on the unchanged canonical `generate`/`schedule_profile` API. This family validates
its own seed/count/settings boundary strictly; that does not clear the old audit.
See `workspace/parametric/README.md` for grammar, limits and replay commands.

## Known limits and open findings

The generator intentionally models only the canonical palette `{0,1,2,3}`, one edge marker, horizontal length-3 bars in normalized coordinates, 4–8 active turns, and at most six inert bars. It does not claim support for malformed markers, arbitrary bar lengths, additional colors, or universal identifiability beyond the declared rivals. The inherited scalar-call audit remains open; it is separate from parametric label and teaching checks.
## Current reviewer considerations

Source SHA-256: `4189136b4e863e70bf07ee2466d865493554544a72273e4f3918da61da7f7c26`.

# Decisions for defba1ab4f90

## D1 — Replace the imported sampler instead of repairing its motif table

**Prior choice:** a 13×13 local-rewrite texture with `grid_size`, palette, and blank-patch controls.

**New choice:** a constructive stream scene matching the canonical transformation.

**Reason:** the prior source was not a noisy version of the same task; it represented a different mechanism, could omit the red entry marker, and failed 8/12 baseline stages. Incrementally widening its motif table would preserve the wrong inductive bias. Evidence: `checks/before/checks/defba1ab4f90_before_battery_summary.json` and `workspace/generator.before.py`.

## D2 — Normalize left entry by transposition, with an explicit chirality sign

The canonical rule has one geometric mechanism viewed in two orientations. In normalized top-entry coordinates, blue uses signed step `+1`; after transposing a left-entry input, blue must use `-1` because transposition mirrors handedness. Keeping this sign explicit makes the common “transpose without chirality flip” shortcut independently testable. Evidence: `counterexamples/left_chirality.json` and the `no_left_chirality_flip` rival.

Rejected alternative: implement independent horizontal and vertical walkers. That duplicates logic and risks silently assigning the same color handedness in both frames.

## D3 — Construct the path before the obstacles

The sampler first chooses turn colors and a bounded column walk, then derives the active bar starts, traces the exact intended path, and finally adds path-disjoint distractors. This makes `orientation`, normalized dimensions, turn count, and distractor count exact by construction.

Rejected alternative: randomly place bars and rejection-sample until the stream happens to be valid. That would make hard overrides unreliable, obscure the accepted distribution, and create seed-dependent failure tails.

## D4 — Use five observable exact axes only

The public axes are:

- `orientation`: `top|left`
- `flow_length`: 19..29 in normalized coordinates
- `lane_width`: 10..15 in normalized coordinates
- `n_turns`: 4..8
- `n_distractors`: 0..6

Each is recovered from output pixels by `observe_overrides`. No decorative “texture” or palette selector is exposed because the canonical task assigns semantic roles to colors and bars. The exhaustive final override stage accepted 35,730/35,730 draws across 397 cases and three bands.

## D5 — Keep production geometry canonical-shaped but permit bounded override expansion

Default profiles use normalized `(22,12)`, `(19,13)`, and `(29,13)`, which cover the canonical shapes and make `MIN_STRICT_FRAC=1.0` honest. Explicit overrides permit 19–29 by 10–15 to test geometric generalization without leaving the ARC 30×30 limit.

Rejected alternative: sample every size uniformly by default. It would reduce canonical support and teach size variation more strongly than the rule’s color/chirality distinction.

## D6 — Four-slot teaching schedule, three demonstrations

The deterministic profile order is top, left, top, left. Every consecutive three-example window therefore includes both orientations. Every active scene contains both blue and green events, so color semantics are visible without relying on a rare sample. Difficulty offsets rotate the same roles instead of changing the rule.

The lesson contract requires three demonstrations and refutes two declared competitors: color-independent steering and no chirality flip for left entry. A 300-lesson census found no survivors in production order or 1,200 held-out query rotations. This does not prove uniqueness against undeclared hypotheses.

## D7 — Distractors are path-disjoint length-3 bars

Unhit bars test whether the solver follows the stream rather than recoloring every colored object. They are placed on rows not used by active bars and disjoint from the traced path. Their colors vary independently.

Rejected alternative: allow overlapping or edge-clipped generated distractors. The authority can process some such cases, but they make the object grammar and the meaning of a “bar” less legible without adding a new rule branch.

## D8 — Synchronize the selected base authorities, not the canonical rule

The canonical ledger and rule hash `c58d2da3a0e5` remain unchanged. The augmented selected base record contained a stale local-rewrite program and was replaced with the same canonical stream program already used by the training selected source; both records now declare their selected roles. This repairs source selection while preserving the intended transformation.

Rejected alternative: leave the divergent file and force the generator to match whichever source happened to win runtime selection. That would train the wrong task and keep labels dependent on authority ordering.

## D9 — Keep a task-local independent oracle and counterexample

`workspace/reference_probe.py` does not call the generator’s `rule_mirror` when computing expected outputs. It provides a second implementation for canonical parity and distribution observations. `counterexamples/left_chirality.json` makes the most subtle orientation error small and replayable.

## Known limitations

- Only palette `{0,1,2,3}` and one non-corner top/left red marker are in domain.
- Generated bars are normalized horizontal length-3 objects; other lengths are untested.
- Active-turn support is 4–8 and distractor support is 0–6.
- The semantic claim is relative to the declared rivals and selected authority, not all possible programs.
- Query rotations reuse each materialized four-pair lesson; they do not enumerate every possible cyclic sampler start.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/defba1ab4f90/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
