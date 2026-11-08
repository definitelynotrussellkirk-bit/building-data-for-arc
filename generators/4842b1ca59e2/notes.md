# Review notes — 2026-10-08

Assignment `review-a21d73d006bfef3e`; selected task `4842b1ca59e2`.
Baseline generator SHA-256:
`05ce37c4cdca4160a25b32fbe6bb7bca0b6df8a954571bff538d659f0ffcdf41`.
Final generator SHA-256:
`ef33c3cb5dee1b3f479bcf27f6122ffcfe74dfd2f1dfce09aed2f1adccd5de74`.
Canonical rule hash: `977235c720d6`. No Racket or canonical puzzle bytes changed.

## Reversed prior choice

Version 2.0.1 described the task as retaining one sparse top cell and deleting
lower cells. Its validator rejected all four canonical inputs unless some column
had multiple seeds, and several advertised palette/texture controls were inert.
The retained audit `review-9e5284a260d20a42:v0001` was used as a lead and its
A2/A3 findings were independently reproduced by the before battery. The new
choice follows the actual authority: the first nonzero seed in a column paints
the whole column, while an empty column stays zero.

## Current sampler

Version 3.0.0 constructs 4..8 by 5..9 zero-background grids with 2..4 active
columns. Topmost colors are distinct. Every ordinary draw has 1..2 stacked
columns of depth 2..3; each lower seed differs from the controlling top seed and
reuses another active top color. This makes the transformation visible while the
validator still accepts the canonical one-seed-per-column cases.

The five public controls are exact and observable: `grid_h`, `grid_w`,
`active_columns`, `stacked_columns`, and `stack_depth`. Unknown, mistyped, and
out-of-range controls fail loudly. Default height/width/palette profiles are
anchored to the four canonical profiles in every difficulty band.

## Teaching contract

Both declared shortcuts fit all four canonical pairs:

- `single_seed_columns_only`: ignore every multi-seed column.
- `bottommost_seed`: fill from the final rather than first seed.

Every ordinary draw contains a stacked column and a top/bottom color conflict,
so both shortcuts are contradicted in every demonstration. The exact retained
counterexample is `counterexamples/canonical_shortcuts.json`; its Python mirror
matches exact Racket execution and both rivals differ on the stacked column.

## Evidence

- Before battery was interrupted after decisive failures: lint lacked `RULE_HASH`,
  self-check rejected 4/4 canonical inputs, defect lint found dead/overlapping
  controls, and profile floor found 0/60 exact canonical profiles.
- Final battery: 12/12 green at the final source hash.
- Exact override matrix: 11,790/11,790 accepted draws, zero findings.
- Semantic census: 600/600 strict-lawful draws; both witnesses fired on 600/600.
- Lesson census: 300/300 three-demonstration lessons, 1,200 pairs, 1,200/1,200
  held-out query rotations, zero declared-rival ambiguity, 1,187 unique inputs.
- Focused task tests: 40/40 passed in the isolated task-test runtime.
- Post-repair visible-only episode: 3/3 visible examples in one revision; earlier
  rule exposure was declared honestly and no reference was consulted during solve.

## Limits

This is a reviewed finite extension, not a proof over all possible column grids.
Default stacks are contiguous; gapped stacks, arbitrary lower colors, repeated
top colors, more than four active columns, and larger canvases are outside the
current sampler. Those restrictions could support undeclared hypotheses on a
broader downstream domain. The retained declared-rival and rotation checks prove
only the tested curriculum policy, not uniqueness against every program.
## Current reviewer considerations

Source SHA-256: `ef33c3cb5dee1b3f479bcf27f6122ffcfe74dfd2f1dfce09aed2f1adccd5de74`.

# Decisions — `4842b1ca59e2`

## D1 — Follow the authority, not the baseline description

**Original choice:** version 2.0.1 said to keep only the top sparse cell and erase
lower cells. The original rationale is unknown; associated notes are empty.

**Chosen:** pin `RULE_HASH = "977235c720d6"`, describe the actual rule, and use an
independent Python mirror only for tests and diagnostics. The selected Racket and
canonical files remain byte-identical to the baseline.

**Alternatives rejected:** changing the authority to match the prose; preserving
the old prose while relying on Racket labels; or treating all four canonical
validator rejections as an intentional opt-out. Each would hide rather than repair
the source/domain mismatch.

**Probe:** the before self-check rejected 4/4 canonical inputs; final rule smoke,
authority sync, and all four canonical-pair tests pass.

**Failure mode/limit:** the mirror is not a second authority. Exact Racket apply and
authority-sync evidence remain the basis for parity claims.

## D2 — Use a small exact grammar instead of decorative controls

**Original choice:** nine axes mixed real dimensions/counts with ignored palette,
position, density, and texture names. Several accepted values were byte-identical.

**Chosen:** retain only five observable integer controls: height, width, active
columns, stacked columns, and stack depth. Validate difficulty, names, types, and
ranges before drawing. All declared joint combinations are constructive.

**Alternatives rejected:** keeping aliases as no-ops; silently clamping impossible
values; or adding palette controls that do not affect the intended rule. A smaller
truthful API is safer for curriculum assembly.

**Probe:** 131 override cases × 30 seeds × 3 bands = 11,790 scheduled and accepted
draws, with zero mismatches, crashes, warnings, or findings. Unknown-key probes
were rejected.

**Failure mode/limit:** the grammar intentionally caps grids at 8×9 and active
columns at four. It is not a claim that the authority fails outside those limits.

## D3 — Preserve canonical support while adding contrastive evidence

**Original choice:** random 4–7 point clouds; no exact canonical-profile branch.
The before profile floor measured 0/60 exact hits.

**Chosen:** default dimensions and active-color count come from the four canonical
profiles in every band. Within those profiles, ordinary draws add one or two
multi-seed columns whose lower colors conflict with their top seed.

**Alternatives rejected:** exact reproduction of canonical grids, which would
retain the ambiguity; large unconstrained random grids, which weaken profile
support; or a degenerate identity curriculum.

**Probe:** final profile floor is 20/20 exact hits in each band (60/60 total), and
all four canonical inputs are accepted. The semantic gate measured 600/600 strict
lawful draws.

**Failure mode/limit:** every default draw is deliberately contrastive rather than
a natural-frequency model. Difficulty changes profile weights and stack counts,
not the conceptual rule.

## D4 — Target the strongest canonical-fitting shortcuts

All four canonical pairs have one seed per active column, so two strong rivals
fit every label: ignore multi-seed columns, or let the bottommost seed win.

**Chosen:** declare both as `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and
`LESSON_COMPETITORS`; pair them with executable stacked-column and color-conflict
witnesses. Every ordinary draw refutes both, so any three-demonstration lesson
contains multiple counterexamples.

**Alternatives rejected:** declaring generic geometric transforms that canonical
pairs already refute; naming rivals without executable outputs; or relying on
witness frequency without checking assembled lessons.

**Probes:** both rivals fit 4/4 canonical pairs. The semantic gate found each
witness in 600/600 draws and verified 60/60 sampled witness/rival disagreements.
The wide census found 0 ambiguous production lessons and 0/1,200 ambiguous query
rotations.

**Failure mode/limit:** this is finite rival coverage. A broader input domain could
support undeclared rules involving gaps, repeated top colors, or arbitrary lower
colors.

## D5 — Three demonstrations and arbitrary held-out position

**Chosen:** keep `EXAMPLES_NEEDED = 3`. Since every generated pair individually
refutes both declared rivals, ordered production lessons and any one-pair holdout
are identifiable against that set.

**Alternatives rejected:** increasing demonstration count to mask weak individual
examples; assuming production order implies rotation safety; or calling the smoke
sample universal evidence.

**Probes:** exhaustive task-local checks cover 16 four-pair windows per band and
all four query positions. The shared required-rotation smoke checks 48 positions;
the source-bound wide census checks 1,200 positions.

**Failure mode/limit:** the census reuses each materialized bundle for rotations
and does not enumerate every possible program or every cyclic schedule start.

## D6 — Keep the authority unchanged

The generator defect was sufficient to explain the mismatch. No canonical output
was wrong, and the exact authority already handled both single and multiple seeds.
Changing Racket would have expanded scope and risked invalidating correct labels.
Final authority sync reports one exact/normalized group and execution parity PASS.

## D7 — Preserve failures and keep audit work separate

The red focused run (35 failed, 5 passed) is retained as test-first evidence. The
partial before battery remains marked incomplete. Audit targets `f9dd4cf0f344` and
`7f31c4f794b2` were inspected and exercised but not edited; their findings are
reported separately in `AUDIT.md` and do not become repair claims for this task.
