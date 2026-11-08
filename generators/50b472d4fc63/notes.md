# Working notes: 50b472d4fc63

## Prior lead

I used `review-88c10647a6e11300:v0001` only as a lead, then remeasured the selected baseline (`generator.py` SHA-256 `cd5f15b38cc8d36ea2f6f57948e537d420815da455adc6c7efc662b91ed8b909`). That audit showed that the wrong rule “mark the endpoints of every three-cell nonzero occupancy block, ignoring color” fit all 3 canonical pairs and that 0/300 sampled baseline defaults supplied a mixed-color exact-three counterexample.

## Baseline reproduction

The completed before battery is retained under `checks/before-complete/`. It reported 7 green stages, 2 advisory stages, and 3 failures:

- lint: no `RULE_HASH`, plus unprobeable/dead axes;
- defect lint: degenerate texture/domain overlap, dead texture controls, and declared ranges not sampled;
- override contract: 23,353 findings over 142,020 draws, including silently accepted unknown keys and many unhonored exact controls;
- semantic gate: no contract (advisory on the baseline);
- canonical-profile floor: the hard band had zero exact canonical-profile support (advisory on the baseline).

## Repair decisions

1. Pin the unchanged canonical authority hash `9af5ed1251ca`; do not modify Racket.
2. Make every default example contain a mixed-color exact-three block, because this is the minimal direct witness against the reproduced color-blind shortcut.
3. Keep true targets as maximal same-color length-three runs and add exact-length boundary negatives. The first repair scheduled short and long negatives once per three samples, which passed the shared census but failed a later all-query-rotations probe in 67/400 rotations per band when the sole length-four witness became the query. Version `3.2.0` instead alternates long and short negatives, giving two of each in every four sequential pairs while keeping canonical-profile examples at three occupancy blocks.
4. Use exact canonical dimension profiles on three of four defaults; reserve the fourth branch for broader dimensions, palette sizes, and upper count bounds.
5. Replace decorative/dead axes with seven pixel-observable controls. Reject unknown, wrong-type, and out-of-range overrides rather than clamping or silently ignoring them.
6. Add task-local independent oracles, declared semantic witnesses/rivals, a canonical-shortcut declaration, lesson identifiability, mutation fixtures, and a cyclic query-rotation probe.

## Final measurements

Final generator version `3.2.0`, SHA-256 `7d9f7e5ba49c3aeab74d8b07a6a5e28d13c15b4209f35373e62b38fa4b3f2b5b`:

- after battery: all 12 stages green;
- portable selected-task tests: 60/60 passed;
- semantic gate: strict 459/600 (76.5%), 3/3 canonical accepted, 3/3 witnesses firing, 12/12 sampled lessons identifiable;
- profile floor: 47/60 exact-profile and 48/60 canonical-envelope hits;
- override matrix: 40,230/40,230 draws accepted across 447 cases, with unknown keys rejected;
- lesson census: 300/300 lessons materialized, 1,200/1,200 unique inputs, 0 ambiguous, 0 hook warnings, 0 scoring errors, and every declared rival refuted in every lesson;
- task-local rotation probe: 100 windows and 400 query rotations per band, with zero failures.

## Limits

The finite semantic checks cover declared rivals, not all possible wrong programs. Defaults intentionally use isolated vertical occupancy blocks of lengths two through four and reserve input color `8`; they do not attempt to teach unrelated component interactions. Exact overrides may deliberately remove teaching negatives, while the default lesson schedule preserves them. Approval and masked-query scoring remain maintainer-owned.
## Current reviewer considerations

Source SHA-256: `7d9f7e5ba49c3aeab74d8b07a6a5e28d13c15b4209f35373e62b38fa4b3f2b5b`.

# Decisions for 50b472d4fc63

Each item records the selected input-design choice, its original rationale, alternatives considered, the probe that informed it, and remaining limits. Finding IDs match `REVIEW.md`.

## D1 / F-01 — Mixed-color exact-three negative in every default

**Choice.** Every default input contains at least one contiguous three-cell nonzero column block whose colors are not all equal.

**Original rationale.** Prior return `review-88c10647a6e11300:v0001` identified a canonical-fitting wrong rule that ignored color changes. I reproduced the premise: the rival fits all 3/3 canonical pairs, while the baseline defaults had no direct counterexample.

**Alternatives.** Make the witness rare; add it only on hard; rely on the canonical examples; or vary target colors without creating a mixed block. Those options leave many lessons ambiguous or fail to distinguish occupancy from same-color runs.

**Probe/failure mode.** The independent `occupancy_exact_three_output` rival differs from the authority on every repaired default. The semantic gate observed the witness in 600/600 samples, and the 300-lesson census refuted the rival in 300/300 lessons.

**Limit.** This targets the strongest reproduced shortcut, not every possible color-sensitive program.

## D2 / F-02 — Alternate length-two and length-four negatives

**Choice.** Even sample indices receive one same-color length-four negative; odd indices receive one same-color length-two negative. Exact overrides can still request either, both, or neither.

**Original rationale and revision.** Version 3.1.0 used a period-three schedule (`short` at one residue, `long` at another) to keep some examples at two blocks. That passed the fixed-query census and every consecutive three-demo window. The required task-local cyclic probe then showed 67/400 failures per band when the only long witness was rotated into the query. Version 3.2.0 alternates the negatives, giving two of each in every four-pair window; removing any one query leaves both boundaries in the three demonstrations.

**Alternatives.** Put both negatives in every input; use probabilistic sampling; or keep the period-three schedule and document the rotation gap. Both-in-every-input was unnecessarily dense, random sampling cannot guarantee lesson support, and retaining a known rotation failure would lower training quality.

**Probe/failure mode.** `checks/tdd-red-query-rotations.log` is the failing regression. `checks/lesson-probe-final.json` checks 400 rotations per band with zero failures after the change.

**Limit.** Four-pair robustness is finite and specific to the declared rivals. It does not prove every arbitrary lesson assembly is identifiable.

## D3 / F-03 — Canonical profiles on three of every four draws

**Choice.** Sample indices not congruent to 3 modulo 4 use one of the exact canonical shapes `(9,6)`, `(8,7)`, or `(9,9)` and a two-color foreground. The fourth branch uses difficulty-aware dimensions and scheduled palette sizes 2–4.

**Original rationale.** The baseline hard band had zero exact canonical-profile support in its 20-draw check. The repaired sampler needed broad axis coverage without drifting away from the small public examples.

**Alternatives.** Always use canonical shapes, fully random dimensions, or separate profile-only generators. Always-canonical would leave advertised ranges untaught; fully random caused profile starvation; a second generator would complicate selection and lesson assembly.

**Probe/failure mode.** Final profile floor: 47/60 exact-profile and 48/60 envelope hits, with support in every band. Distribution lint reports generated component-size median 3 and no morphology drift flag.

**Limit.** The 3/4 mixture is a deliberate curriculum prior, not an estimate of a natural task distribution.

## D4 / F-04 — Compact target and mixed-block counts

**Choice.** Canonical-profile draws use one true target plus one mixed-color negative and one alternating length negative. The broad branch uses two true targets and two mixed negatives plus one length negative.

**Original rationale.** An intermediate repair generated six to eight vertical blocks and triggered a corpus-density concern. The public examples have roughly two foreground components, so richer teaching should remain visually compact.

**Alternatives.** Maximize all counts on every input; sample counts independently; or use only one target/one negative everywhere. Maximal density moved too far from the corpus; independent counts made lesson guarantees harder; fixed minimal counts did not exercise upper override values.

**Probe/failure mode.** `checks/tdd-red-distribution.log` and `checks/tdd-red-compactness.log` preserve the failed iterations. Final component-count median is at most 3 in the task tests and passes the shared drift gate.

**Limit.** Broad-branch inputs are intentionally denser than canonical-profile inputs.

## D5 / F-05 — Isolated vertical occupancy blocks

**Choice.** Place each feature in a distinct column, as one contiguous block of length 2, 3, or 4, at a random legal row start.

**Original rationale.** This gives a direct, readable distinction between same-color maximal runs and color-changing occupancy blocks while avoiding accidental merges that would make exact overrides unobservable.

**Alternatives.** Allow multiple separated blocks per column, touching horizontal objects, or arbitrary noise. Those are authority-lawful in some cases but add segmentation ambiguity unrelated to the repaired shortcut and complicate exact count recovery.

**Probe/failure mode.** `observe_overrides` independently recovers all seven axes from pixels. The override gate accepted 40,230/40,230 draws across 447 cases.

**Limit.** Defaults do not teach interactions with horizontal touching or multiple blocks in one column. This is an explicit generator-domain restriction and is not a claim about all grids the Racket program can execute.

## D6 / F-06 — Palette policy and reserved output color

**Choice.** Inputs draw from `{1,2,3,4,5,6,7,9}` with exact palette sizes 2–4; color `8` is reserved for output endpoints. A two-color mixed witness uses `A,B,A`; larger palettes expose additional colors in the mixed block.

**Original rationale.** Reserving `8` keeps the transformation visually and semantically unambiguous. Palette-size scheduling guarantees support instead of relying on chance.

**Alternatives.** Permit input 8; force two colors only; or choose palette size randomly. Input 8 obscures changed cells, two colors leave the declared range dead, and random scheduling can miss an advertised value in small gates.

**Probe/failure mode.** Palette sizes `{2,3,4}` appear in every 80-example test census; malformed inputs containing 8 are rejected.

**Limit.** The generator does not explore cases where an unchanged input already uses the highlight color.

## D7 / F-07 — Seven exact, pixel-observable public axes

**Choice.** Keep only `grid_h`, `grid_w`, `n_targets`, `n_mixed`, `n_short`, `n_long`, and `palette_size`. Reject unknown keys, booleans masquerading as integers, and out-of-range values. Declare no incompatible combinations because all valid combinations fit the minimum 6-column grid.

**Original rationale.** The baseline exposed decorative texture/palette/position axes, silently swallowed typos, clamped or rejected advertised ranges by difficulty, and lacked an observation hook.

**Alternatives.** Retain old axes as diagnostic aliases; silently clamp; or declare most combinations incompatible. Those choices preserve misleading API surface or make controls unfalsifiable.

**Probe/failure mode.** The baseline override gate found 23,353 findings. The final gate reports PASS over 40,230 draws, 447 cases, and three bands; unknown keys are rejected.

**Limit.** Removing old axes is an intentional API cleanup for this unapproved generator, not backward compatibility.

## D8 / F-08 — Executable semantic contract

**Choice.** Declare three witnesses and three rivals, identify the color-blind rival as the canonical-fitting shortcut, and implement `lesson_identifiable` against the current `LESSON_COMPETITORS` mapping.

**Original rationale.** Morphology and diversity checks cannot establish that examples teach the intended rule. The baseline semantic gate had no contract.

**Alternatives.** Document rivals only in prose; hard-code rival names in tests; or rely on solve success. Prose is not executable, copied lists drift from source, and a single solve is weaker than deterministic contrast checks.

**Probe/failure mode.** Final semantic gate: 3/3 witnesses firing, 3/3 rival claims verified, and 12/12 sampled lessons identifiable. Both the shared census and task-local probe iterate declarations dynamically.

**Limit.** The rival set is finite and reviewer-authored; undeclared programs may still fit.

## D9 / F-09 — Leave the Racket authority unchanged

**Choice.** Pin `RULE_HASH = "9af5ed1251ca"` and change only the sampler, validation, semantic metadata, tests, and workspace tools.

**Original rationale.** Supported authority execution and all canonical pairs agreed with the intended exact same-color length-three rule. The defect was missing teaching support, not wrong outputs.

**Alternatives.** Rewrite the rule for clarity or alter canonical data. Either would introduce needless authority risk and exceed the evidence.

**Probe/failure mode.** Rule smoke, Racket lint, and authority sync pass. Authority sync notes one archival divergent copy but execution parity passes and selected active sources are synchronized.

**Limit.** This review does not reconcile the archival divergent source because only selected task files may be edited.

## D10 / F-10 — Independent probes and TDD evidence

**Choice.** Put independent rule/rival logic in `workspace/reference_probe.py`; add `workspace/lesson_probe.py` for reusable fixed/rotated lesson checks; keep 60 portable tests under the selected task's `tests/` directory.

**Original rationale.** Tests should not validate production helpers with themselves, and future agents need a repeatable way to catch lesson-position gaps.

**Alternatives.** Test only internal helpers, add ad hoc notebooks, or rely exclusively on shared gates. Those options are harder to replay or miss the exact rotation issue found here.

**Probe/failure mode.** Red logs preserve missing-contract, density, compactness, query-rotation, and missing-tool failures. Final portable snapshot passes 60/60. A fresh-extraction replay applies the final patch and reruns the selected task tests.

**Limit.** The independent Python authority transcription is test support, not the production label source; Racket remains authoritative.
