# a5bda33d14a0: current contract and evidence

## Rule and exact controls

Canonical Racket remains the labeling authority: find the global bounding box of all nonzero input cells, paint its zero perimeter cells 8, and preserve existing source colors and the interior. The canonical rule is unchanged (`eb3c0d7afaf9`; full source SHA-256 `eb3c0d7afaf96dbf2ce5bc4afa73690c430ad8b202fee8d81913742c3d4c0067`).

The selected generator is version `2.0.1`, SHA-256 `8095c7fca8bafafd63c796287fe7bba7ca1a85ea39b51542b868d913630192f5`. Its four exact integer controls are `grid_h=4..18`, `grid_w=4..18`, `n_cells=3..12`, and `n_distinct_colors=2..9`. Distinct colors **include background 0**; sources use 1..7 or 9. Booleans, strings, and floats are rejected. An explicit color count cannot exceed an explicit cell count plus one; this incompatibility raises an exception carrying the two axis names. A lone color-count override adjusts the default cell count when necessary.

Retired misleading controls `palette_kind`, `palette_size`, `position_bias`, `density`, and `texture` now raise clear errors, as do unknown keys. Degenerate textures are no longer a supported generation path. Difficulty is categorical: `None`, `easy`, `medium`, or `hard`; numeric difficulty is rejected. It changes default sampling preferences, while exact dimension overrides retain the full declared range.

Each valid input has a source box at least 3×3, an empty perimeter cell and an empty interior cell. These conditions distinguish the intended operation from identity and filled-box rivals. `self_check` validates shape, strict color types, source count, box geometry and both empty-cell requirements. `observe_overrides` measures all four controls from pixels.

## Teaching distribution and lesson policy

The old forced NW/SE-corner pair with exactly three differently colored sources has been replaced by sparse and distributed-extrema profiles. Sparse defaults use three sources, four total colors and canonical canvas profiles. Distributed defaults vary source count, palette, box size and location, and put extrema on four sides without occupied corners. Sparse examples retain several corner configurations and orientations.

The production declaration is **three demonstrations plus one query**, with schedule period **4**. Profile choice depends on `(seed + sample_index) % 4`, giving two sparse and two distributed pairs in every four consecutive default positions. This supports the declared first-three, row-endpoint, filled-box, border-overwrite and canvas-border rival checks. Exact overrides are input controls; universal lesson identifiability under every override combination is not claimed.

## Observed verification and limits

The final native battery in `WORK/checks/after-final` reports all **12 stages green**, bound to the selected source above. Its override matrix recorded **80,640 attempts**, **79,290 accepted draws**, **1,350 structured incompatible-count rejections**, and zero findings or warnings. Canonical rule smoke executed 120 cases without crashes, identity outputs, out-of-bounds results or input mutation. The strict semantic census accepted 600/600 generated inputs and all five canonical inputs.

The source-bound fixed-seed schedule receipt exercised all four starts at seed 0 in easy/medium/hard: **12 lessons and 48 query rotations**, with zero ambiguity. The separate `WORK/checks/lesson-census.json` materialized **300 lessons**, 100 per difficulty, with **1,200 unique inputs and 1,200 query rotations**, zero materialization/scoring errors and zero declared-rival ambiguity. Its hashed seed recipe and requested starts 0..99 differ from exhaustive schedule enumeration; its reporting modulus 6 is not the generator's period 4. These are finite rival checks, not a proof over all seeds, hypotheses or teaching policies.

The independent final distribution probe (`WORK/checks/focused/final-probe.json`, seed 1729, indices 0..127) had 128/128 valid draws, 60 canvas shapes, all counts 3..12 and all source-palette counts 1..8. NW/SE pairs occurred 10/128 times and the row-first/last shortcut matched 17/128, versus 128/128 for both in the retained baseline. The probe uses explicit Python hypotheses; native correctness evidence comes from the separate Racket checks.

The episode-level border-color extension in `workspace/parametric/` remains a **proposed authoring prototype**, with no production integration or approval. Its ordered lesson checks do not establish query-rotation identifiability. Canonical border color 8 and canonical rule ownership remain unchanged.
## Current reviewer considerations

Source SHA-256: `8095c7fca8bafafd63c796287fe7bba7ca1a85ea39b51542b868d913630192f5`.

# Decisions — a5bda33d14a0

Assignment `review-1fe8e6e6e8fd3ff4` and packet identity remain unchanged. The pinned
baseline was version 1.1.1, SHA-256
`57bef3d349f7c489707ee8d7994a91bf740876871a3f12e754482e71843f4f83`.
No prior review index existed for this task and its associated-notes ledger was
empty; no historical return was used as evidence of the selected baseline.

## M1: Broaden support while retaining canonical examples' characteristics

**Prior choice.** Always sample exactly three differently colored sources, placing
one at each of the NW and SE corners and one inside. The notes provided no
empirical rationale for treating those restrictions as essential. In the retained
seed-1729, index-0..127 baseline census, all 128 draws had this configuration.

**Decision.** Keep a sparse profile with three sources and four total colors at
one of the five canonical canvas shapes, but vary side extrema, orientation,
palette and position. Mix it with distributed inputs of four through twelve
sources and one through eight source colors. This retains exact canonical-profile
support while exposing the all-source bounding-box rule.

**Rejected alternatives.** Keeping only three points can never distinguish the
first-three shortcut, which fits 5/5 canonical pairs. Unrestricted independent
random points alone would provide only probabilistic lesson-level witness
coverage. Removing sparse examples entirely risks losing the canonical profile
floor. Always using corner-free inputs would introduce another artificial
invariant; sparse examples therefore retain varied corner configurations.

**Evidence.** `checks/focused/final-probe.json` records 128 valid draws, 60 shapes,
all supported counts and palettes. The paired baseline/final row-endpoint match
count falls from 128 to 17, and NW/SE presence falls from 128 to 10. This is a finite
same-seed comparison, not a population success probability or model accuracy gain.

## M2: Make the override interface observable and literal

**Prior choice.** Advertise endpoints broader than the sampler's difficulty
bounds, silently ignore controls, and coerce floats/booleans/strings. Exact
`n_cells=8` could return three sources, and advertised 4×4 could reject.

**Decision.** Expose only four measurable integer controls: height, width, source
cell count and distinct color count including background. Honor their full stated
ranges independently of difficulty. Reject unknown/retired controls, nonliteral
integers, and impossible explicit count pairs; the latter exception identifies
`n_cells` and `n_distinct_colors`. A lone color count may adjust the default source
count to remain feasible. Do not silently repair explicit contradictory requests.

**Compatibility decision.** Remove `palette_kind`, `palette_size`, `texture`,
`position_bias` and `density`. Numeric difficulty is intentionally no longer
accepted: only `None`, `easy`, `medium`, `hard` are valid. The initial 54-case test
source accepted numeric 0.25/0.75; those two expectations were removed when this
contract was narrowed, while the original test bytes and results were preserved.
This is a disclosed API change under version 2.0.1. A future shared numeric
difficulty convention would require a deliberate compatible implementation and
updated checks; it is not approximated by accepting just the previous test values.

**Evidence.** The final matrix covers 896 cases, 30 seeds and 3 bands: 79,290
successful exact draws and 1,350 structured incompatibility rejections, no findings.
`tests/test_distribution.py` measures controls from pixels. Tests also check
determinism, malformed input validation and explicit boundary combinations.

## M3/M4: Teach the rule in the actual lesson assembly

**Policy.** Three ordered demonstrations plus one query, made from consecutive
default sample indices; arbitrary one-pair query holdouts are supported for the
tested rivals while the remaining demonstration order is preserved.

**Decision.** Declare period four and use `(seed + sample_index) % 4` to give two
sparse and two distributed examples in every four-position window. Distributed
examples reserve all four corners empty and put nonzero extrema on each side;
any three points therefore miss at least one extremum. Every input leaves an empty
interior and an empty perimeter cell. Source colors on the perimeter distinguish
overwriting, and sparse boxes smaller than the canvas distinguish canvas borders.

**Iteration.** The first repaired battery exposed invalid scalar handling and a
missing explicit schedule receipt. A focused seed-10/index-2 sparse example also
showed that a full-canvas box did not itself refute the canvas-border rival.
`checks/focused/lesson-contract-red.txt` retains the 16-fail/5-pass run and grid.
The final generator forces non-full-canvas sparse defaults when feasible and
retains full-canvas fallback for dense exact overrides. After this repair, the
73 canonical-generator regression cases passed; the complete portable suite,
including the four prototype cases, passed 77/77.

**Evidence and limits.** The final semantic gate requires rotation identifiability
and enumerates all four starts at fixed seed 0 across three bands (12 lessons,
48 rotations, 9 unique inputs). The separate larger census tests 300 hashed-seed
lessons (100 per band), 1,200 distinct inputs and 1,200 rotations, with zero
declared-rival ambiguity or scoring/materialization errors. The larger sampler's
modulus 6 is a reporting choice, not a claim to enumerate the generator's period.
The finite results support five unique declared rivals, not universal induction,
all possible random seeds, arbitrary lesson sizes or every explicit override.

## Domain and authority

The canonical Racket program is unchanged and pinned by `RULE_HASH`. The ordinary
input domain excludes cyan source cells, all-zero inputs and degenerate boxes;
it requires a box at least 3×3 with both an empty perimeter and empty interior.
These constraints make the selected operation observable. They are sampling
choices, not revisions to the wider canonical function. Independent Python
implementations are used only to measure hypotheses; actual Racket outputs bind
the smoke checks, semantic lessons and parameter evidence.

## Parametric assessment: proposed runnable border-color variant

A single output-color parameter is a small, auditable extension: choose it once
per episode and replace only the known output-color literal in the canonical
program. Default 8 returns the exact original text. The input grid never includes
the chosen output color in the retained examples, so demonstrations show which
color is being introduced. The public JSON contains demonstrations and query
inputs only; private authoring evidence holds parameters, rules, hashes and labels.

The runnable `workspace/parametric/prototype.py` retains complete episodes for
settings 8, 3 and 6 at seed 104729. Actual Racket execution produced 12 chosen-rule
pairs and 72 rival/demo evaluations, refuting 24 alternative-setting/episode
combinations. Four focused tests check all five canonical labeled pairs and 36
all-color/edge combinations. Exact program hashes and retained instances are in
`checks/parametric/evidence.json`.

This remains **proposed**, with three ordered demonstrations and the last pair as
query. Rotation identifiability is unknown. Only border-color rivals were tested;
the prototype still has restrictive source-palette and opposite-corner geometry.
It does not inherit the repaired canonical generator's broader teaching claims.
A second parameter was not added: fill-vs-outline or conditional source recoloring
would change more semantics and require additional discriminating support, which
the current bounded extension does not establish.

The original shared `wrap_rule` call failed on a repository-layout import of
`scripts.comment_solutions`; the task-local ordinary-Racket binding workaround is
covered by actual canonical equivalence tests. A later 30-second startup timeout
under contention was retained and resolved with a local 120-second startup limit.
No shared library or canonical authority was patched to make the prototype pass.

## Audit and solve boundaries

The two random audits are source-bound findings only; `AUDIT.md` distinguishes
domain/contract defects from incorrect labels and unverified training admission.
The blind solve was completed before any repair-source exposure. The post-repair
solve has honest earlier exposure `yes`, no reference consultation during solving,
one genuine attempt and 3/3 visible passes. Both hidden query verdicts are unknown.

Large before/census evidence is compressed losslessly with original names, sizes
and hashes in `checks/LARGE-EVIDENCE.compression.json`. Failures and full instances
remain reconstructible; no rerun substitutes for the original evidence bytes.

## Final replay and transport

The exact builder delta was applied to a full fresh original extraction, with Git
initialized at that extraction's WORK root and the root equality checked explicitly.
All nine changed/new paths matched the recorded hashes before and after the fresh
77-case suite; every test passed. The initial extraction-stage inode failure was
preserved and resumed only after rechecking the complete original packet. To fit
filesystem capacity, the validated original ZIP and builder checkpoint protected
all source while redundant isolated copies were removed; the tested fresh repo
was then moved back without byte changes. See `checks/replay/verification.json`
and `relocation.json`. No shared source or patch-generation rule was relaxed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-af8033c6ab6dbbfd:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `8095c7fca8bafafd63c796287fe7bba7ca1a85ea39b51542b868d913630192f5`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported bounded no-new-issue result on unchanged8095c7fca8bafafd63c796287fe7bba7ca1a85ea39b51542b868d913630192f5. 64 native cases/38 unique inputs include48 default draws and16 exact endpoints. All64 actual Racket outputs match independent perimeter implementation, requested controls and validator; eight invalid calls rejected. Twelve default three-demo lessons and48 reused query rotations refute declared rivals. Canonical first_three rival fits5/5 labeled canonical pairs,32/64 generated cases; counts are not model accuracy. No all-seed/tuple/undeclared-rival claim or override-level teaching guarantee. Source-bound report, cases, actual labels, commands and assessment retained in generators/a5bda33d14a0/evidence/bounded-audit-af8033c6ab6dbbfd/manifest.json.

### Assessment or prior finding

## a5bda33d14a0

**No issue found within bounded independent checks.** Audited generator v2.0.1,
SHA-256 `8095c7fca8bafafd63c796287fe7bba7ca1a85ea39b51542b868d913630192f5`. No audited source, reference authority or approval was changed.
The canonical Racket execution reports rule hash `eb3c0d7afaf9` and executed
rule-text SHA-256 `df988c659488b6100c933d7726d54bfa38d21ad77263db4d78a18610121a6a4b`; exact native outputs, input hashes,
generator hash and command are retained in `checks/audit/a5bda33d14a0/racket.json`.

**Concrete risks checked.** I inspected exact-control feasibility at dense 4×4
boundaries, palette/count compatibility, malformed scalar handling, preservation
of sources and interior zeros, and whether the repaired schedule still teaches
the all-source perimeter against its actual declared rivals. The compact
reproducer is `checks/audit/a5bda33d14a0/probe.py`; execution records are in
`checks/audit/a5bda33d14a0/commands.json`.

The probe generated **64 cases, 38 unique input grids**: 48 default draws from
seeds 0–3, indices 0–3, and easy/medium/hard, plus 16 exact-boundary draws from
seeds 100–115, index `(seed-100) % 4`, difficulty cycling easy/medium/hard.
Boundary requests exhaust dimensions (4,4), (4,18), (18,4), (18,18), cell counts
3 and 12, and total-color counts 2 and min(9, n_cells+1). All 64 were deterministic,
passed the selected self_check, and matched every requested measured control.
Eight targeted malformed/contradictory calls were rejected, including boolean
seed/index/dimension, negative index, unsupported numeric difficulty, dimension
19, unknown axis and n_cells=3/n_distinct_colors=9; the last rejection names both
incompatible axes. Exact seed/request/observed values are in
`checks/audit/a5bda33d14a0/cases.json`, with full inputs in `inputs.json` beside it.

Supported `arcpuzzles apply --check-generator-domain` executed canonical Racket
on all 64 cases: **64/64 outputs matched an independent pixel-based global-box
perimeter implementation, zero execution errors or domain-check failures**.
The declared canonical shortcut `first_three` fits all **5/5 canonical labeled
pairs**, as checked directly; on these 64 generated cases it matches 32/64.
The other actually declared lesson competitors match row_endpoints 13/64,
filled_box 0/64, overwrite_border 0/64, and canvas_border 2/64. These are explicit
rival counts, not an estimate of model accuracy.

**Lesson policy and verdicts.** Three demonstrations plus one query are formed
from consecutive default indices 0–3; production uses the fourth pair as query.
Across seeds 0–3 and three bands, **12/12 production lessons** had no declared
rival fitting every demonstration while disagreeing on the query. Preserving
order of the other three demonstrations and holding out each of the four pairs
also passed **48/48 query rotations**, zero ambiguities. These windows reuse the
48 default case positions and do not represent 48 additional unique inputs.
`checks/audit/a5bda33d14a0/assessment.json` retains every query case and its rival
ambiguity list, exact source/rule hashes, and all denominators.

**Limits and domain.** These finite, small-seed checks do not prove absence of
other shortcuts, identifiability for undeclared rivals, behavior at all seeds or
indices, every valid override tuple, or arbitrary lesson assembly. The current
notes explicitly reserve lesson guarantees for default generation, so exact
boundary cases were checked for input/label correctness rather than being
silently promoted to an override-level teaching guarantee. No reproduced bug,
suspected shortcut needing a finding, or new domain question arose in this audit.
This is findings-only evidence; it does not approve the generator for training.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
