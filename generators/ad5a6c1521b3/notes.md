# Current notes: `ad5a6c1521b3`

Current version: **3.0.1**. Current generator SHA-256:
`44ddc5e354aecb7ada959800234c1d8aac482d28d13af8cf3144c3ede5d44cd4`.
Canonical authority is unchanged and remains pinned by
`RULE_HASH = "8e796791a1a2"`.

The retained v3.0.0 review used as a lead was
`review-db74ecbe04172c16:v0001`, source SHA-256
`e3ff9c9b2eedbf0aefcec8bc4faf15189ab6714f0103b3570a9a856ef9ae8bfa`.
Current measurements were rerun against v3.0.1 rather than inherited from that return.

## Intended rule

The unique modal color is background. For each other color independently, find its
4-connected components. A color with one component is unchanged. For a split color,
select the largest component; equal-size components are resolved by the greatest
(top row + left column) score. Erase all old cells of that color, then fill the
winner's bounding rectangle plus the adjacent column on its left.

## Production distribution retained from v3.0.0

The earlier v2.1.0 proxy used one foreground color on zero background and could not
represent the canonical tie, nonzero background, irregular winner, passive distractor,
three-component, or independent two-color branches. V3.0.0 replaced it with four
constructive, pixel-recoverable profiles:

- `tie_both_8`;
- `single_unique_8`;
- `tie_both_16_three`;
- `single_unique_16`.

A deterministic schedule, three demonstrations, seven palettes, role swaps, safe
translation, and branch-preserving reflection expose the named semantic rivals while
retaining nuisance variation. `scene_profile` remains the only advertised exact
control. This review did not reverse those choices.

## Current repair: strict public scalar contract

**Prior behavior.** V3.0.0 accepted booleans, floats, numeric strings, and negative
sample indices, creating aliases at the public generation boundary. The before battery
was 11/12 green; `defect_lint` reported 33 findings.

**New behavior.** V3.0.1 requires exact integers for `seed` and `sample_index`, and a
nonnegative `sample_index`. Coercion was rejected because it would preserve aliases.
No distribution, profile, schedule, output label, canonical text, or `RULE_HASH` was
changed. Focused tests observed the invalid-call cases red before and green after.

## Parametric proposal (not production)

A runnable isolated prototype lives in `workspace/parametric/`. It introduces one
once-per-episode parameter, `expansion_side`:

- `left`: exact canonical/default program;
- `right`: identical background/component/tie/erasure/bbox logic, with the adjacent
  expansion column on the right.

The prototype pins the canonical text hash, obtains labels from instantiated Racket,
requires bilateral in-bounds clearance and nonoverlapping transformed rectangles, and
redacts hidden parameter/program/seed/query-answer information from public episodes.
Two deterministic four-pair episodes show all three demonstrations refuting the
opposite setting. This proposal does not alter production `generate()` or authority.
Evidence: `checks/parametric/expansion-side-v1/` in the current return.

## Final verification

- final strict battery with fixed-seed enumeration of all declared schedule starts:
  **12/12 green** (`checks/after-enumerated/`);
- selected portable task tests: **65/65 passed** (`checks/task-tests/`);
- source-bound census: **300/300** three-demo lessons materialized, **0** production
  ambiguities, and **0/1,200** ambiguous query rotations against declared rivals
  (`checks/lesson-census.summary.json`);
- post-repair visible-only solve: **3/3** demonstrations passed, bound to the current
  generator hash (`solve/summary.json`).

The first final-source after battery without schedule enumeration is intentionally
retained as evidence: it had 11 green stages and only the explicit
`declared_period_not_enumerated` warning; its 12/12 production lessons and 48 rotations
had no ambiguity. The enumerated rerun closed that evidence gap without source changes.

## Assumptions and known limits

- The production sampler is a four-profile curriculum, not an exhaustive lawful-grid
  generator.
- Generated active winners deliberately expose a bbox hole and a visible adjacent
  column so the transformation is observable.
- All bands share the semantic profile set; difficulty changes nuisance geometry, not
  the underlying rule.
- Finite declared-rival checks do not prove unique induction against every possible
  hypothesis.
- The parametric prototype covers two deterministic episodes and the opposite-side
  rival; it is proposed authoring evidence, not variant approval.

No blocking finding remains for the current selected source.

## Current owner source and evidence limits

Accept exact-integer seed/index and nonnegative-index validation. Signed integer seeds remain legal. Canonical Racket unchanged. VERSION3.0.0->3.0.1 participates in gen_ctx/stable_rng: accept as an explicit keyed random-stream migration,not same-seed byte-identical grids despite unchanged sampling-law wording. Reviewer reports final12/12 battery with fixed-seed full period enumeration,65 portable tests repeated after full94130-file replay,300 lessons/1200 rotations/562 unique inputs and no declared-rival ambiguity or hook warnings. Earlier11/12 non-enumerated battery retained as an evidence gap subsequently addressed on unchanged source. Isolated left/right expansion prototype has two Racket-labelled3-demo/1-query episodes;every demo refutes opposite setting. Bilateral-clearance/nonoverlap support is a declared prototype limitation;finite seeds/rivals only. No production variant API,variant approval or training admission. Tests,labels and census remain reviewer-reported;owner verification here checks hashes and structure.
## Current reviewer considerations

Source SHA-256: `44ddc5e354aecb7ada959800234c1d8aac482d28d13af8cf3144c3ede5d44cd4`.

# Decisions for `ad5a6c1521b3`

## D1 — Reject ambiguous scalar calls rather than coerce them

**Finding.** The pinned v3.0.0 generator accepted `True`, `False`, floats, numeric
strings, and negative sample indices. Python's `bool`/`int` relationship and implicit
RNG coercions made these calls aliases rather than independently meaningful samples.
The before battery recorded 33 strict defect-lint findings.

**Choice.** At the start of `generate`, require `type(seed) is int`, require
`type(sample_index) is int`, and require `sample_index >= 0`; bump only the generator
version to 3.0.1.

**Rejected alternatives.** Coercing with `int(...)` would preserve accidental aliases;
letting `gen_ctx` decide would leave behavior dependent on downstream implementation;
and changing the sampler would be unrelated to the reproduced defect.

**Probe.** `tests/test_call_contract.py` was run before the repair and failed all 11
parameterized cases (`checks/tdd/call-contract-red.log`), then passed after the repair
(`checks/tdd/call-contract-green.log`). The complete portable task suite is 65/65.

**Limit.** This intentionally says nothing about large but valid integers; deterministic
hash/RNG behavior for exact integers remains the existing contract.

## D2 — Use one rule parameter: expansion side

**Purpose.** The original-family priority asks for a small extension that preserves the
reasoning pattern. The meaningful local choice is which adjacent column accompanies
the selected component's filled bounding box.

**Choice.** `expansion_side` has two values:

- `left` — exact canonical/default program;
- `right` — the same component selection, tie-break, erasure, and bbox fill, with the
  extra column on the right.

The value is selected once per episode. The prototype reuses production inputs only
when every active winner has clear in-bounds columns on both sides and transformed
rectangles remain nonoverlapping. Labels come from the instantiated Racket source, not
a Python mirror.

**Rejected parameters.** Changing the component-size criterion or tie-break would
alter the core object-selection reasoning; changing the number of components is an
input-distribution axis rather than a rule parameter; changing expansion width adds a
counting task and weakens fidelity to the supplied family. Combining multiple
parameters would create unnecessary cross-products before one-axis coherence was
established.

**Evidence.** Red-before-source and green-after-source tests are retained in
`checks/tdd/parametric-red.log` and `checks/tdd/parametric-green-attempt1.log`.
`checks/parametric/expansion-side-v1/report.json` records two settings, exact Racket
hashes, one four-pair episode per setting, all three demonstrations refuting the rival,
and query disagreement.

**Limit.** The prototype tests two deterministic episodes and the opposite-side rival;
it does not establish support for all seeds or all alternative hypotheses. The side is
made visible in every demonstration, so this is a coherence/authoring prototype rather
than a deliberately difficult latent-parameter lesson.

## D3 — Keep canonical authority and production generation unchanged

The v3.0.0 sampler was already an approved, branch-covering repair from prior return
`review-db74ecbe04172c16:v0001`. The current defect was at the Python call boundary,
not in the labels, Racket rule, distribution, or lesson schedule. Therefore the
canonical text, `RULE_HASH = "8e796791a1a2"`, profiles, palettes, and schedule remain
unchanged. The parametric source lives only under `workspace/parametric/`.

## D4 — Enumerate the declared schedule instead of changing it

The first final-source after battery reported 12/12 production lessons identifiable
and 0/48 ambiguous rotations, but warned that the declared period had not been
exhaustively enumerated. Because this was an evidence gap, not an observed teaching
defect, the chosen response was a fresh full battery with
`--enumerate-schedule-period --schedule-seed 0`. That run is 12/12 green. Altering or
removing the truthful schedule declaration merely to silence the warning was rejected.

## D5 — Retain finite-rival limits explicitly

The 300-lesson census refutes every declared rival in production and all 1,200 query
rotations, but this is not a proof of unique induction. Reports therefore state the
exact demonstration count, ordering/rotation policy, source/rule hashes, denominator,
and the distinction between a four-profile curriculum and the broader lawful domain.

## D6 — Audit targets remain untouched

The two assigned audits produced actionable evidence against current source hashes:
pre-final panels are dead context in `generic_waypoint_route_gen1`, and all advertised
degenerate texture overrides leave `5c6e1b7fd77a`'s own domain. Audit work is reported
in `AUDIT.md` and `checks/audit/`; no changes were made to either target.
