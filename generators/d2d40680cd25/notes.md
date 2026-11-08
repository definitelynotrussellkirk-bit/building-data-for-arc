# Working notes: d2d40680cd25

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `4c0151e11fbbe18a423daae4feb00fd1e88cf368789535da3f6b1e8737d906df`.

# Decisions: `d2d40680cd25`

## D1 — Preserve the canonical/Racket authority

**Input evidence.** The immutable baseline rule hash was `09ddc1726a80`. Baseline rule smoke passed, canonical outputs were reproduced, and authority sync reported exact synchronization for selected active sources plus execution parity `PASS`. The retained note `GNOTE-001553` likewise treated the differing `raw_code` as archival rather than active authority.

**Choice.** Leave `repo/shared/data/canonical/puzzles.jsonl`, the selected target, and archival source untouched. Pin and retain `RULE_HASH = "09ddc1726a80"` in the generator.

**Rejected alternatives.** Rewriting the Racket source for style, normalizing the archival source, or changing the canonical row would add authority churn without addressing either measured advisory.

**Probe.** Before and after full batteries include `rule_smoke`, `racket_lint`, and `authority_sync`; the final battery is 12/12 green.

**Failure mode / limit.** Textually divergent archival source remains present by design. Any future authority edit must rerun exact sync and execution parity.

## D2 — Add a linked 40% canonical-profile prior

**Input evidence.** Baseline strict profile support was 2/60 exact and 18/60 envelope, with no exact support in medium or hard. Prior note `GNOTE-001554` specifically requested replay and improvement of this floor.

**Choice.** Add three linked profiles `(9,10,2)`, `(9,11,3)`, and `(10,12,3)` and select one on 40% of default draws using a keyed `canonical_profile` RNG stream. These reproduce the three canonical height/width/palette profiles while retaining the existing scene builder.

**Rejected alternatives.** A 100% canonical-only distribution would collapse the broad domain. A fixed periodic schedule would make profile membership easy to infer from `sample_index`. Rejection sampling would consume variable RNG and complicate reproducibility. Independently biasing height, width, and count would create combinations that do not correspond to canonical profiles.

**Probe.** `checks/profile-after-1/` reports 26/60 exact and 36/60 envelope, and the regression suite requires at least 12/64 exact and 16/64 envelope matches in every band.

**Failure mode / limit.** The 40% rate is a curriculum choice, not a claim about the natural ARC distribution. Future changes should preserve both canonical support and unanchored domain breadth.

## D3 — Disable linked anchoring on any linked-axis override

**Input evidence.** `grid_h`, `grid_w`, and `n_blobs` are advertised exact controls. Applying a linked profile after one such override could silently constrain the other axes or replace the requested value.

**Choice.** If any of the three linked axes is explicitly supplied, bypass canonical anchoring and draw all three through their normal `GenCtx` paths. Keep every value typed, keyed, and recorded.

**Rejected alternatives.** Partially anchoring unspecified linked axes would make an override on one axis unexpectedly alter the joint distribution of the others. Mutating the chosen canonical tuple to fit the override would create profiles that were never declared.

**Probe.** `test_exact_overrides_bypass_profile_anchoring` repeatedly requests the high-end `14×14`, four-piece configuration and checks exact observed controls. The full override battery remains green and rejects unknown keys.

**Failure mode / limit.** Explicit overrides intentionally opt out of canonical-profile support; they are diagnostic controls, not guaranteed teaching lessons.

## D4 — Model the strongest canonical shortcut explicitly

**Input evidence.** Canonical demonstrations have a cyan wall but no movable body whose final position proves the wall is collidable. Therefore “remove wall, apply gravity, redraw wall” fits all 3/3 demonstrations.

**Choice.** Implement `_decorative_wall_rival`, declare it under canonical shortcuts, semantic rivals, and lesson competitors, and pair it with a `wall_support` witness. Reuse the existing `rule_mirror` and scene analysis rather than duplicate the intended rule.

**Rejected alternatives.** A prose-only warning would not be checked by the semantic gate. Declaring a rival without first proving it fits every canonical pair would be a strawman. Adding a new generator branch solely for one hand-built witness was unnecessary because ordinary generation already guarantees wall support.

**Probe.** The task test proves canonical fit; the semantic gate observes the witness 600/600; the exact Racket counterexample is retained under `checks/shortcut/`.

**Failure mode / limit.** One executable rival does not exhaust all conceivable shortcuts. The declarations should grow only when a plausible canonical-compatible rival and a lawful witness are both available.

## D5 — Use task-local TDD and leave frozen fixtures untouched

**Input evidence.** The duties prohibit rewriting the baseline root `test_generator_*.py` fixture and require new tests under `tests/`.

**Choice.** Add `tests/test_generator.py`. First run it against the baseline and retain the 7-fail/1-pass red result, then make the smallest generator changes needed to reach 8/8 green.

**Rejected alternatives.** Editing the frozen fixture would invalidate baseline provenance. Writing tests after the implementation would not demonstrate that they detect the missing behavior.

**Probe.** `checks/tdd-red/result.json`, `checks/tdd-green-1/result.json`, `checks/task-tests/result.json`, and `checks/final-replay/task-tests/result.json` preserve the sequence.

**Failure mode / limit.** The tests are targeted regressions, not a replacement for the full inherited battery.

## D6 — Measure lessons, not just individual witnesses

**Input evidence.** A frequent witness does not establish that a complete demo/query lesson eliminates the shortcut before the query. The shared census also does not rotate every pair into the query position.

**Choice.** Run the source-bound production lesson census for 100 lessons per band with three demos and one query, then add a retained three-lesson probe that rotates each of four pairs through the query slot.

**Rejected alternatives.** Reporting only the 600-draw semantic witness count would overstate lesson identifiability. A much larger exhaustive rotation sweep was unnecessary once every pair in the retained lessons independently refuted the sole declared rival.

**Probe.** `checks/lesson-census.json` materializes 300/300 lessons, 1,190 unique inputs, and zero ambiguous lessons; `checks/cyclic-query-rotations.json` reports 12/12 rival eliminations before query.

**Failure mode / limit.** This is finite declared-rival evidence. It does not establish universal identifiability, semantic equivalence classes, or arbitrary nonconsecutive subsets.

## D7 — Bind the post-repair solve to final bytes

**Input evidence.** Solve evidence becomes stale if the generator changes after preparation.

**Choice.** Finish code first, prepare the solve from generator SHA `4c0151e1…d906df`, use only visible examples while solving, and declare earlier rule exposure `yes` because the repair work necessarily exposed the rule.

**Rejected alternatives.** Reusing a pre-repair solve or claiming no exposure would make the record misleading.

**Probe.** `solve/summary.json` and `solve/attempts/0001/report.json` both carry the exact final generator hash and 3/3 visible passes.

**Failure mode / limit.** The solve is reviewer-authored visible-only evidence; it is not a masked-query score or model trace.

## D8 — Keep adversarial audits findings-only

**Input evidence.** The audit draw selected `1d2e86233750` and `eee19c538953`, neither of which is the repair target.

**Choice.** Run their baseline batteries, build exact Racket-backed reproducers, document findings, and leave both source trees unchanged.

**Rejected alternatives.** Fixing them would violate selected-task scope and confound the delta.

**Probe.** `checks/audit/1d2e86233750/counterexample.json` and `checks/audit/eee19c538953/counterexample.json` include source hashes, exact inputs, executed rule hashes, outputs, rival outputs, and domain statements.

**Failure mode / limit.** The first audit proves one surviving finite lesson window, not its frequency. The second demonstrates a canonical/domain boundary defect but does not prescribe the full repair.

## D9 — Replay the exact source delta against the original ZIP

**Input evidence.** The working packet has no repository Git metadata, so a normal commit-based provenance chain is unavailable.

**Choice.** Generate `checks/final-code.patch`, extract the original uploaded ZIP into a clean directory, run `git apply --check`, apply the patch, verify the final generator SHA, and rerun focused tests, profile, semantic, and lint stages.

**Rejected alternatives.** Copying modified files directly would not test patch applicability. Replaying against the already-modified working tree would not be a fresh handoff check.

**Probe.** `checks/final-replay/metadata.json` records original ZIP SHA, patch SHA, baseline/final generator hashes, commands, exits, and evidence paths. The first lint launch was interrupted by the outer batch limit and retained; the isolated lint rerun passed.

**Failure mode / limit.** This replay covers the source delta and focused regressions. The full 12-stage battery was run on the identical final source in the main packet rather than repeated a second time.

## D10 — Keep shared-tool feedback outside the task delta

**Input evidence.** The baseline battery summary correctly said `10 green, 2 advisory`, but the shell's final line said `ALL 12 stages green`.

**Choice.** Supply a small optional patch at `checks/feedback/F1-battery-console-verdict.patch`, but do not edit shared code in the selected-task source delta.

**Rejected alternatives.** Applying the patch directly would violate allowed repair scope. Omitting the contradiction would leave future reviewers vulnerable to reading only the terminal line.

**Probe.** `checks/before/result.json` contains the contradictory stdout; the JSON summary contains the authoritative verdict.

**Failure mode / limit.** Maintainers must decide and integrate the shared patch separately.
