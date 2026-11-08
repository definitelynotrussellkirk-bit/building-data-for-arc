# Working notes: 9ee024f29fdb

## Review `review-d375f053896bbf58`

### Reproduced baseline defects

The pinned baseline generator SHA-256 was
`e8ccd805a267a486c6305ee72c4121392baaf8b1fc085eda964a76e2a5c52512`.
It lacked canonical `RULE_HASH`, declared dimensions in an unprobeable form,
accepted unknown/ill-typed controls, and had no exact observer. At 17×17 with
requested density .55, random/cluster produced 79 cyan cells, but aligned,
column, and row produced only 16/12/12. `self_check` required only one interior
cyan cell and did not reject the all-erased complement. No executable rivals or
shortcut witnesses were declared.

The required full before-battery was interrupted; its `running` receipt is
retained under `checks/before/` and is not called a pass. Focused baseline and
TDD failure evidence is retained under `checks/before-*` and
`checks/tdd-*-red*`. No earlier return was used as a lead; associated notes were
empty.

### Repair

* Bumped generator version to `3.0.0` and pinned `RULE_HASH=82f439b3efb8`.
* Made `grid_h`, `grid_w`, `decoy_palette_size`, and `lattice_noise` exact,
  observable axes. Density/layout are explicitly diagnostic.
* Fixed every layout to realize the same quantized requested cyan count.
* Added canonical-heavy dimension priors without removing any advertised size.
* Alternated a clean canonical profile with a joint counterexample containing
  interior decoys and noisy periodic rows/columns.
* Strengthened validation, added strict canonical support, four rivals, two
  canonical-fitting shortcuts, witnesses, and lesson identifiability.
* Increased `EXAMPLES_NEEDED` from 2 to 3 after a cyclic query probe found
  150/900 harmful rotations under the two-demo design.
* Added 45 task-local tests and a source-bound reusable probe in
  `workspace/reference_probe.py`.

### Final evidence

Final generator SHA-256:
`9eac2ef3eeccac30007686f659f866f5328f153a427955bc36d123a56eb07b9c`.

* Final battery: 12/12 stages green.
* Portable task tests: 45/45 passed.
* Semantic gate: 600 draws, 157 strict hits (26.17%, floor 20%), 0 crashes.
* Profile floor: exact support in all bands (6/20 easy, 5/20 medium, 2/20 hard).
* Lesson census: 300 lessons, 1,200 pairs, 1,199 unique inputs, zero ambiguity.
* Cyclic probe: 300 starts, 1,200 query rotations, zero failures.
* Racket smoke: 120/120 applications, 120 distinct outputs, no mutation/crash.

### Authority synchronization

Canonical behavior did not change. The selected base solution's equivalent
`grid-from-fn` source was replaced with the exact existing canonical `cellmap`
program, and primitive metadata was synchronized. Canonical, raw, and selected
target sources now share the same exact hash and solve all four canonical pairs.

### Limits

The validator intentionally describes the teaching manifold, not every lawful
input to the abstract rule. Density/layout are not inverse-recoverable exact
labels. Finite declared-rival coverage and 1,200 rotations are strong regression
evidence, not a universal induction proof.
## Current reviewer considerations

Source SHA-256: `9e5f37c3717c447b9f65554f0906aa0d85db8d9a247f361fd6998abe116202f6`.

# Decisions for review `review-d35976854c0ea451`

## D1 — Preserve the selected canonical authority

**Decision.** Keep the period-four/cyan-erasure/red-repaint Racket rule exactly
unchanged and retain `RULE_HASH=82f439b3efb8`.

**Why.** Canonical pairs, rule smoke, and authority synchronization already agree;
the defects were in request validation and the generated teaching distribution,
not labels. Changing the authority would expand risk without addressing either
root cause.

**Rejected alternatives.** Encode randomized noise behavior into the rule; change
period or output color in production; rely on a Python mirror as authority.

**Evidence and limits.** Final rule smoke and authority sync are green. The Python
mirror is regression evidence only.

## D2 — Prototype period and repaint color as episode-level parameters

**Decision.** Build a separate prototype with `period∈{3,4,5}` and
`paint_color∈{2,4}`, chosen once per episode. Preserve `(4,2)` as the exact
canonical default and leave the production generator fixed.

**Why.** Both parameters are small, compositional changes to the same reasoning
pattern. Shared inputs expose both: changing period moves cleared lines, and
changing paint changes every surviving non-cyan interior cell.

**Rejected alternatives.** Vary cyan's erase color, choose parameters per example,
or expand to arbitrary periods/colors. Those options change object roles, make
demonstrations internally inconsistent, or enlarge the search space before the
small family is validated.

**Probe and limits.** Six complete episodes, three demonstrations plus one query
each, 24 protected-Racket applications, and five setting rivals per episode are
retained under `checks/parametric/period-paint-v1/`. Four controlled fixtures and
finite rivals do not establish universal identifiability.

## D3 — Move lattice witnesses off selector intersections

**Prior choice.** Version 3.0.0 placed one nonzero marker for each periodic row in
column 0 and one for each periodic column in row 0. This defeated the all-zero-line
rival but created a stronger border-selector shortcut.

**New choice.** For each periodic row, select a nonperiodic column; for each
periodic column, select a nonperiodic row. Use a keyed RNG for positions and
colors. Every line remains visibly noisy, but top/left borders no longer encode
the complete selector sets.

**Rejected alternatives.** Remove lattice noise, always fill all periodic cells,
or merely randomize colors at the old locations. Those respectively restore the
zero-line ambiguity, distort morphology, or preserve the selector channel.

**Probe and failure modes.** The retained counterexample differs from the wrong
border rule at 61 cells and passes `self_check`. This refutes the named shortcut,
not every conceivable coordinate hypothesis.

## D4 — Retain the discovered shortcut as executable curriculum evidence

**Decision.** Add `border_marker_lattice` to `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and the nonzero-lattice witness contract rather than only
adding a one-off unit test.

**Why.** A regression test prevents this exact source bug; an executable rival
also checks every sampled lesson and query rotation. It converts historical audit
evidence into an ongoing training-data contract.

**Rejected alternative.** Keep the rival only in prose or hard-code rival names in
a probe. The chosen declarations are discoverable by shared gates and task-local
tools.

## D5 — Reject malformed requests and singleton-signal lessons

**Decision.** Require literal integer seed, nonnegative literal integer
`sample_index`, and difficulty in `{None,easy,medium,hard}`. Require at least two
interior cyan cells both in generation and `self_check`.

**Why.** The defect gate reproduced 48 accepted invalid scalars and a singleton
minimal impostor. The minimum is compatible with every canonical example and
with all default density bands; the 5×5/0.10 override now rounds up to two.

**Rejected alternatives.** Waive defect-lint warnings, add only tests without
changing behavior, or claim the singleton is lawful. The canonical data does not
need a singleton grammar, and accepting malformed request metadata weakens
reproducibility.

**Probe and limits.** Eighteen tests were observed failing before the patch and
passing after it. The validator still intentionally describes the teaching
manifold rather than every abstract-rule input.

## D6 — Keep three demonstrations and test both production and rotations

**Decision.** Retain the existing three-demo lesson requirement and alternating
clean/counterexample schedule. Report ordered production and arbitrary query
rotations separately.

**Why.** Any three consecutive demonstrations contain a joint counterexample,
while the clean profile preserves canonical support. The final census sampled
300 production lessons and all 1,200 query positions; the cyclic probe exhausts
300 deterministic starts and the same 1,200 rotations.

**Limit.** Zero ambiguity against declared rivals is not proof against undeclared
rules. Downstream assemblers should preserve three demonstrations unless they
rerun identifiability checks.

## D7 — Treat interrupted and intermediate checks as evidence, not passes

The required before battery was interrupted by the execution caller and remains
`status=interrupted`. An intermediate after source completed 11/12 stages and
failed defect lint; it motivated D5. Only the fresh `checks/after-final/` run is
reported as the final battery pass. This distinction avoids upgrading partial or
stale evidence by implication.

## 2026-10-24 native period/paint parametric upgrade

The existing task-local prototype now has a native `adapter.py` and
`promotion.json` contract for the six Cartesian settings
`period ∈ {3,4,5}` and `paint_color ∈ {2,4}`. The default `(4,2)` remains the
canonical Racket program byte-for-byte. Inputs are sampled independently from
settings, support 2–6 demonstrations and 1–4 queries, preserve the same first
query across query-count requests, and include a substantive 30×30 fourth query.
Every example constructively distinguishes all declared settings.

The bounded adversarial pass repaired the old one-query gallery and its
setting-associated ordinal names. A later packet-level export audit caught two
additional identity defects shared by the assigned writers: pretty-printed bytes
with truncated IDs, followed by a nonconforming `arc-` prefix. The final writer
retains four distinct queries, emits exact `public_challenge_bytes` under
`challenge-<full-sha256>.json`, and leaves the visible ID unchanged when private
query answers mutate; the official helper passes all ten retained public episodes
across the three assigned tasks. All six settings × seven examples were executed
through bundled Racket (42 applications) and matched the Python oracle. The
complete task-local suite passed 70 tests. Native qualification passed 12/12
setting/seed jobs for seeds 0 and 17 with 3 demos and 4 queries. Evidence is under
`WORK/checks/parametric/9ee024f29fdb-period-paint-v2/` and
`WORK/checks/parametric/9ee024f29fdb-qualification/`; the current source-bound
inventory hash is `de2fe9fd33c07ce6469ed302229713966cbeb0beec5525c5e15e7880b3bdb14c`.
This is still a proposed family, not acceptance or training admission.
