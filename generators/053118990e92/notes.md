# Working notes: 053118990e92

## Review 2026-10-04

Baseline generator SHA-256:
`9e22c439a887682bfed1a19da2fc7643c0434b1b95bb59626fb2ab747a8e4da6`.
Final generator SHA-256:
`894119384c9fb8dcad2199804ed001620049ef94de168c614c34fd2da0949a14`.
No prior return or associated note was used as a lead; the imported associated
notes file was empty.

The baseline lacked `RULE_HASH`, mixed invalid pseudo-textures into the ordinary
domain, silently accepted unknown override names, rejected advertised values in
specific difficulty bands, and had no executable semantic contract. The repair
uses five exact observable axes, four scheduled teaching profiles, four executable
witnesses/rivals, and a source-bound cyclic query probe.

A first repaired schedule remained ambiguous when the sole same-color-tie pair was
moved to the query. The final profiles deliberately overlap witnesses, and the
100-seed-per-band probe now reports 6,000/6,000 identifiable rotations. A later
battery run caught a constant sample-index-0 canonical anchor; its geometry is
kept but seed colors now vary within 2–7.

The selected Racket behavior was not changed. The task-local base authority file's
`target_code` differed from its existing `raw_code` only by a comment; the comment
was synchronized and final authority execution parity passed. See `DECISIONS.md`
and `REVIEW.md` in the packet root for the full rationale and retained evidence.
## Current reviewer considerations

Source SHA-256: `894119384c9fb8dcad2199804ed001620049ef94de168c614c34fd2da0949a14`.

# Decisions for 053118990e92

## Evidence used

No prior reviewer return was available as a lead. The imported
`evidence/associated_notes.jsonl` was empty, so every defect claim was re-measured
against the packet's pinned baseline generator
`9e22c439a887682bfed1a19da2fc7643c0434b1b95bb59626fb2ab747a8e4da6`.
The partial before battery and the focused before gates are retained under
`checks/before*`; prior claims were not treated as measurements.

## D1 — Preserve the canonical transformation

**Choice.** Keep the selected Racket behavior unchanged. The rule uses the bbox of
all color-8 cells, treats every other nonzero interior cell as a seed, fills by
Manhattan nearest distance, leaves a tie blank only when the nearest colors
differ, and fills same-color ties.

**Rationale.** Canonical rule smoke already passed and all five canonical inputs
were accepted by the validator. The observed failures were sampling, declaration,
and curriculum failures—not incorrect canonical outputs.

**Authority text synchronization.** The task's archived base JSON had `raw_code`
and `target_code` with identical behavior but one comment difference. I removed
that comment from `target_code`, making both task-local source fields identical.
No Racket expression, canonical row, output, or rule hash changed. Final authority
sync reports execution parity PASS.

**Rejected alternative.** Rewriting or beautifying the Racket program would add
semantic risk without fixing the generator's actual defects.

## D2 — Replace pseudo-textures with exact semantic axes

**Choice.** The public control surface is now:

| Axis | Exact valid domain | Reason |
| --- | --- | --- |
| `grid_h` | 9–14 | Covers all public heights while guaranteeing room for a useful bbox interior. |
| `grid_w` | 11–16 | Covers public widths and supports the compact metric/tie witness geometry. |
| `n_seeds` | 2–4 | Matches the intended task family and canonical complexity. |
| `frame_style` | `ring`, `corners` | Directly controls the key bbox-vs-full-ring distinction. |
| `seed_color_mode` | `distinct`, `duplicate_pair` | Directly controls whether same-color nearest ties can occur. |

Every Cartesian combination is constructive in every difficulty band. Unknown
keys are rejected, invalid values raise, and `observe_overrides(grid)` recovers the
realized values so the gate can detect fallback or clamping.

**Original rationale.** Unknown. The baseline used a `texture` axis containing
`single_seed` and `broken_frame`, but `single_seed` contradicted its own
`self_check`, `broken_frame` was lawful rather than degenerate, and the axis made
`n_seeds` inert in mixed cases.

**Rejected alternatives.** I did not retain compatibility aliases for the broken
textures because that would leave ordinary-domain values with contradictory
meaning. I also did not declare broad incompatibilities: the compact geometry can
honor every advertised combination exactly, which is simpler and more useful for
deterministic data construction.

## D3 — Difficulty changes defaults, never legality

**Choice.** The legal domains above are identical for `None`, `easy`, `medium`,
and `hard`. Difficulty only biases ordinary defaults toward larger grids and more
seeds; an explicit valid override is always honored in every band.

**Rationale.** The baseline declared broad valid ranges but rejected them in
specific bands, causing 2,043 override findings over 22,590 draws. A training or
review tool should be able to request a boundary value without knowing hidden
band-specific clamps.

**Rejected alternative.** Narrowing each axis declaration by difficulty would
make the current contract pass but would reduce joint support and make curricula
harder to control. Exact cross-band legality is both cheaper to explain and easier
to test.

## D4 — Use four overlapping teaching profiles

**Choice.** Default sample indices cycle through:

1. `canonical_ring`
2. `different_color_tie`
3. `same_color_tie`
4. `corners_manhattan`

The first two profiles include a different-color nearest tie and a cell whose
Manhattan and Euclidean winners differ. The final two include a duplicate-color
pair, a different-color competitor, and the metric distinction; corners-only
frames appear in two profiles. `EXAMPLES_NEEDED` remains 4.

**Rationale.** The canonical pairs leave at least two shortcuts fully consistent:
"all ties blank" and "require a full ring." A useful generated lesson must refute
those shortcuts and also teach different-color tie behavior and Manhattan rather
than Euclidean distance.

**Probe-driven revision.** The first schedule put each rare branch in exactly one
profile. A cyclic test showed that moving `same_color_tie` into the query left all
four demos compatible with `ties_always_blank` (seed 0, schedule start 0, query
offset 2, in every band). The final layout overlaps witnesses across profiles, so
removing any one pair still leaves every declared rival refuted. This was verified
for 6,000 rotations rather than inferred from marginal witness frequency.

**Rejected alternatives.** Increasing the lesson to five or more demonstrations
would have hidden a brittle curriculum instead of repairing it and would increase
training cost. Randomly hoping for rare witnesses was rejected because a finite
lesson needs deterministic semantic support, not only good pooled frequency.

## D5 — Keep a strict canonical-profile anchor, but vary it lawfully

**Choice.** `canonical_ring` uses a 10×12 full-ring geometry and colors drawn in a
seed-dependent order from the public 2–7 palette. Geometry is stable enough to
supply strict canonical support; ordered colors vary across seeds.

**Rationale.** The profile floor and strict semantic gates need real linked support,
not separate morphology marginals. The first implementation fixed both geometry
and palette, causing the self-check diversity probe to see one identical sample-0
grid across 40 seeds. Palette permutation removes that collapse without weakening
the teaching witness or leaving the canonical palette.

**Rejected alternatives.** Removing the anchor would lower canonical support;
randomizing every structural dimension would make strict-profile support
accidental. Replaying a canonical input was also rejected—the generator creates
new instances rather than copying public examples.

## D6 — Define executable semantic evidence

**Choice.** The generator exports:

- `strict_canonical_like`
- `SEMANTIC_WITNESSES`
- `LESSON_COMPETITORS` / `SEMANTIC_RIVALS`
- `CANONICAL_SHORTCUTS`
- `lesson_identifiable`
- `rule_mirror`

The witnesses are small predicates over actual input/output pairs. Rivals are
complete executable transformations. Before using a rival as a "canonical
shortcut," the task-local probe verifies it against every usable canonical pair.

**Rationale.** Names and comments are not evidence that a generated lesson teaches
a rule. Executable rivals let the same pair be scored under the authority mirror,
and exact failing cells can be materialized.

**Limitation.** `rule_mirror` is a Python audit mirror, not a second authority. Its
high-volume results are accepted only alongside independent Racket rule-smoke and
authority-parity gates. The rival set is finite and cannot prove universal
identifiability.

## D7 — Build task-local cyclic coverage tooling

**Choice.** Add `workspace/cyclic_lesson_probe.py`. It imports the selected source,
reads live declarations rather than copying names, verifies canonical shortcut fit,
constructs five-pair windows for every schedule start, rotates each pair into the
query, and emits exact generator/input hashes plus ambiguity reproducers.

**Rationale.** The shared `lesson-census` intentionally tests the production
assembly policy but does not rotate every pair into the query. That omission was
material here: marginal witness coverage looked healthy while one legal query
position left a shortcut alive.

**Portability.** A task test imports and executes the probe inside the materialized
portable runtime, so missing workspace packaging was itself caught by a red test
before the final pass.

## D8 — Tests and retained failures

Production changes followed test-first cycles. Retained red evidence includes:

- initial contract expectations: `checks/tdd-red-command.log`
- cyclic lesson hole: `checks/tdd-red-cyclic-command.log`
- missing portable workspace tool: `checks/tdd-red-probe-command.log`
- constant canonical anchor: `checks/tdd-red-default-diversity-command.log`
- the intermediate 11/12 battery: `checks/after-final/`

The final test suite has 26 tests covering exact boundaries in all bands, unknown
and invalid overrides, determinism, global-RNG purity, fresh return values,
malformed grids, strict support, all semantic witnesses/rivals, every cyclic query
rotation, source-bound tool declarations, and default-anchor diversity.

## D9 — Domain limits and failure modes

- Grids outside 9–14 by 11–16 are intentionally not generated, even if the Racket
  rule could evaluate them.
- Only 2–4 seeds are generated; one-seed cases do not teach tie semantics and were
  removed from the ordinary domain.
- Exact `n_seeds=2` combined with `duplicate_pair` remains lawful but may remove
  some profile-specific witness coverage. The default curriculum—not every manual
  override combination—is what the lesson-identifiability claim covers.
- Finite declared-rival checks can miss undeclared shortcuts, and unique grid hashes
  do not imply semantic independence.
- The repair does not approve the generator for training; catalog status remains a
  separate maintainer decision.
