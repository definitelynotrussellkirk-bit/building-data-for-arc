# Working notes: 55993f4c12af

## 2026-10-04 review `review-43d4fa117b675f45`

Lead used: unverified prior audit `review-c3c6fa8c032ee1d2:v0002`, source SHA-256
`a4ac6959566b93f299e214db681bdcc66de9132d8e7b6fdff1b74b06ab2a0e92`.
It reported 121/1,500 sampled lessons where a top-half-only rival fit all three
demonstrations and failed the query. The current packet baseline independently
reproduced the underlying shared-support construction and four battery blockers.

The generator was rebuilt as version `3.0.0` around one invariant: every ordinary
input contains all four aligned occupancy states (`00`, `10`, `01`, `11`). The
public surface is now only five exact, observable controls. A four-slot schedule
keeps an exact canonical anchor at 25% while every three-demo sliding window also
contains an off-canonical example. The semantic contract declares executable
rivals, witnesses, canonical-fitting shortcuts, and `lesson_identifiable`.

Intermediate failures retained in `checks/` drove three corrections: paired
palette defaults looked like an alias, a five-slot anchor produced only 20%
canonical-profile support, and naive heavy counts on the 3x3 minimum could be
observationally balanced. Final source SHA-256 is
`f5bc92f43afad9f059e3e88e54a89e4bb12f5c246cd9d2729edaeae0933ed722`.
The final battery is 12/12 green, task tests are 52/52, the production census is
0/300 ambiguous, and the cyclic probe is 0/300 ambiguous.

The canonical Racket behavior was not changed. The bound base `raw_code` and
active `target_code` text were synchronized exactly to the canonical program,
with matching primitive-chain metadata, to remove authority drift.
## Current reviewer considerations

Source SHA-256: `f5bc92f43afad9f059e3e88e54a89e4bb12f5c246cd9d2729edaeae0933ed722`.

# Design and review decisions for 55993f4c12af

## Scope and evidence policy

The selected generator, its task-local tests/workspace/notes, and the bound base
solution were the only source components changed. The canonical rule behavior was
kept fixed. Prior audit `review-c3c6fa8c032ee1d2:v0002` was treated as a lead and
all final claims were remeasured on this packet's source. Failed and intermediate
checks were retained rather than overwritten.

## D1 — Put the complete Boolean truth table in every ordinary input

**Original rationale:** unknown. The old pattern/density machinery appears to
have aimed for visual variety, but frequently reused identical panel support.

**Choice:** construct exact counts for `00`, `10`, `01`, and `11`, with every
count positive, then shuffle their positions.

**Alternatives considered:**

- Merely reduce the probability of identical support. Rejected because a small
  residual rate still produces mislabeled teaching lessons at scale.
- Rely on a multi-example schedule to eventually show bottom-only/overlap cells.
  Rejected because a single weak lesson can still train the shortcut and because
  the task is cheap enough to identify per example.
- Keep arbitrary texture families and add post-hoc rejection. Rejected as harder
  to observe, test, and guarantee than constructive relation counts.

**Probes/failures:** the prior audit's top-only rival was the root lead. New tests
assert that top-only, bottom-only, XOR, and AND differ from the intended output on
320 generated grids. The production and cyclic lesson probes find 0/600 combined
ambiguous windows.

**Limitation:** this makes the Boolean operation clearer than a sparse natural
sample might. It is deliberate data-quality bias toward falsifiability.

## D2 — Replace broad/fictitious axes with five exact controls

**Original rationale:** the old `palette_kind`, pattern, density, texture, and
`or_target` controls likely attempted broad combinatorial coverage. Several were
unobservable, dynamically bounded, aliases, or invalid in the ordinary domain.

**Choice:** expose only `half_h`, `grid_w`, `top_color`, `bot_color`, and
`relation_profile`. Validate types and full declared ranges before drawing;
reject unknown keys; make equal colors an explicit incompatibility; recover every
accepted value with `observe_overrides`.

**Alternatives considered:**

- Preserve old names as no-op compatibility aliases. Rejected because accepting
  an exact-looking control without changing output is worse than a loud break.
- Keep `or_target` as a dynamic numeric axis. Rejected because target count alone
  does not identify which truth-table rows are taught and its prior declared range
  disagreed with branch-local draw bounds.
- Keep invalid textures under `DEGENERATE_TEXTURES`. Rejected because the shared
  override gate exercises public values through the normal validator; invalid
  diagnostic grids should not masquerade as trainable data.

**Probes/failures:** TDD began with 28 failures. The full override matrix later
found two additional boundaries: `bot_color=3` collided with the anchor's default
top color, and heavy profiles on the 3x3 minimum observed as balanced. Both cases
were made red tests before their fixes. Final result: 53,280 accepted draws and
900 declared incompatibility rejections, no findings.

## D3 — Four-slot schedule with a 25% exact canonical anchor

**Original rationale:** canonical examples are all 12x4 with top/bottom colors
3/5, so some exact support is needed; generating only that profile would create
fixed-shape and fixed-palette shortcuts.

**Choice:** slot 0 is an exact 12x4, colors-3/5 anchor. Slots 1–3 use banded
noncanonical widths and independently keyed colors. Every three-demo sliding
window therefore contains at least two off-canonical examples.

**Alternatives considered:**

- A five-slot cycle. Implemented first, then rejected after the profile-floor gate
  measured 12/60 = 20%, below the required 25% after-phase threshold.
- Random anchors. Rejected because short lessons could miss canonical support or
  accidentally contain all anchors.
- Paired preset palettes. Rejected after lint correctly flagged them as a likely
  one-to-one alias; independent keyed draws preserve real joint support.

**Probes/failures:** final profile floor is 15/60 exact and envelope hits. The
cyclic probe enumerates every start residue and reports 0/300 ambiguous windows.

**Limitation:** the deterministic period is visible to a sufficiently adversarial
learner, although outputs do not depend on slot and all slots obey the same rule.

## D4 — Exact relation profiles, including minimum-size observability

**Original rationale:** unknown; old density/pattern controls were not reliably
recoverable from a grid.

**Choice:** balanced, top-heavy, bottom-heavy, overlap-heavy, and empty-heavy
profiles map to exact occupancy histograms. Heavy profiles keep all four states
and have a unique modal relation even at the 3x3 minimum.

**Rejected implementation:** the first heavy-count formula added too little mass
on 3x3 grids, so `observe_overrides` classified some heavy profiles as balanced.
The override matrix exposed this; a five-profile minimum-grid regression now
locks it down.

**Limitation:** `observe_overrides` is intended for lawful constructed grids. An
arbitrary hand-authored grid with tied nonbalanced leaders is rejected rather
than assigned an ambiguous profile name.

## D5 — Strict structural validator and Python mirror

**Choice:** validate rectangular ARC-color grids, even height, declared dimension
range, exactly one distinct lawful foreground color per half, distinct panel
colors, and complete occupancy support. `rule_mirror` runs only after validation.

**Alternatives considered:** permissive acceptance of canonical-looking malformed
inputs. Rejected because silent acceptance makes source-bound gate results hard to
interpret and lets off-domain examples enter training.

**Tests:** canonical pairs are accepted; ragged, odd-height, boolean, out-of-range,
and missing-relation mutations are rejected without exceptions.

## D6 — Executable semantic contract rather than prose claims

**Choice:** declare live functions for nine lesson competitors, three
canonical-fitting shortcuts, seven witnesses, witness-to-rival claims, and
`lesson_identifiable`.

**Alternatives considered:** a copied list in a one-off report. Rejected because it
would drift from generator source and cannot be exercised by the inherited gate.
The reusable workspace probe iterates the live dictionaries directly.

**Probes:** semantic gate 600/600 strict, 7/7 witnesses, 7/7 claims, 12/12 smoke
lessons; production census 0/300; cyclic probe 0/300. Canonical-fitting shortcut
claims are verified against all five canonical pairs before lesson scoring.

**Limitation:** finite named rivals are not proof against all possible shortcuts.

## D7 — Racket authority text synchronization only

**Original state:** canonical program, selected `target_code`, and bound base text
were behaviorally equivalent but not exact-source synchronized.

**Choice:** copy the canonical program text into the bound base `raw_code` and
active `target_code`, and update primitive-chain metadata. Do not change the
algorithm.

**Alternative:** leave semantically equivalent text divergent. Rejected because
source-bound receipts and future edits would continue to disagree about which
text is authoritative.

**Verification:** rule smoke, grammar, Racket lint, and authority sync all pass;
execution parity reports one distinct source text.

## D8 — Tests and reusable future-agent tooling

**Choice:** add 52 task-local pytest cases and
`workspace/lesson_probe.py`. The probe records generator SHA, declared rivals,
canonical shortcut fit, exact cyclic seeds/starts, unique input hashes, and the
first 25 failures if any.

**Why a separate probe:** the production census uses the real sampler and large
coverage but explicitly does not rotate every pair into query position. The
cyclic tool cheaply closes that task-specific schedule gap.

## D9 — Reapply the exact delta to a fresh original packet

**Choice:** freeze the generated source patch, apply-check and apply it from a
clean extraction of the original upload, then rerun the full inherited battery,
task-local tests, production lesson census, and cyclic schedule probe there.

**Why:** working-tree success can hide unrecorded files, stale runtime state, or a
patch that no longer matches the submitted baseline. A clean replay makes the
return itself, rather than the mutable workspace, the verified unit.

**Verification:** both Git operations exited 0; generator, test, bound base,
workspace probe, and patch hashes matched exactly. The replay battery was 12/12
green, pytest was 52/52, the production census was 0/300 ambiguous with
1,200/1,200 unique inputs, and the cyclic probe was 0/300 ambiguous. The fresh
production report was byte-identical to the earlier final report. Evidence is
under `checks/fresh-replay/`.

## Remaining limitations and stopping reason

- All semantic evidence is finite and source-bound; it does not establish
  universal induction.
- The curriculum deliberately removes the old free-form texture vocabulary. It
  keeps dimension, palette, relation-balance, and randomized-layout diversity,
  which are the task-relevant axes.
- No approval or train-safety state was changed.
- Audit targets `7be1519f847c` and `12b9259f7792` were examined only; their defects
  were not repaired in this assignment.

Stopped after the exact packaged delta independently passed a clean original-packet
replay: full 12-stage battery, 52 task tests, both 300-lesson probes, source-hash
and solve-binding checks, plus the required adversarial audits and reports.

## 2026-10-21 review `review-89b132e69d909e18`

This round used the current selected source as its baseline rather than replaying
older returns. The before battery found one newly blocking defect: 33 strict-scalar
findings because `seed` and `sample_index` were not validated before `gen_ctx`.
Eleven focused regressions were written failing first. Version `3.0.1` now rejects
boolean, float, and string seeds; boolean, float, string, and negative sample
indexes; all earlier grid-generation behavior and canonical Racket authority are
unchanged. Final generator SHA-256 is
`1d38b983e4c7edb9d70d6bfec9877d5b631e4583a1398b8c8383a1d7f0a9a348`.

The final canonical battery is 12/12 green, portable task tests are 112/112, and
the 100-per-band lesson census materialized 300 lessons / 1,200 unique inputs
with zero production ambiguities and zero ambiguities across all 1,200 query
rotations. The final task-local cyclic probe also checked 300 lesson windows
across every schedule start and found zero ambiguities. The fresh visible-only
solve passed all three demonstrations; earlier
rule exposure was declared yes and no source/reference material was consulted
during that solve.

A separate proposed parametric prototype now lives under `workspace/parametric/`.
It varies aligned occupancy operation (`xor`, `and`, `or`) and output color
(`1..9`), with canonical default `or/4`, selecting one rule per episode and using
protected Racket for every label. The retained all-settings audit completed 27/27
settings, matched all five canonical pairs, and found 27 distinct outputs on one
lawful witness. A deliberately incomplete diagnostic leaves `and/3` and `or/3`
ambiguous, confirming the demo-only checker fails honestly. This is finite
proposal evidence only; production generation, rule hash `ce2dee847896`, and
approval state were not changed.

Assigned audits were inspection-only. `c5309d8fa84c` failed five strict battery
stages and has no semantic contract/tests; `7a15f5e5ebd9` passed its semantic and
override checks but accepted 108 invalid scalar values. Shared feedback recommends
centralizing exact scalar validation and providing a reusable finite parametric
episode harness.
