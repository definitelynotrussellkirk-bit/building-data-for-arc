# Working notes: 0eabac67e70a

## Current contract

The selected authority is unchanged and pinned as `RULE_HASH = "4a7acff260a8"`.
For every non-zero color that occurs exactly twice, the Racket rule paints the
sign-step span between those two cells in color 8 on an otherwise blank canvas.
This sampler deliberately emits only horizontal, vertical, and perfect 45-degree
diagonal pairs, for which the second endpoint is on that span.

Version `2.0.0` replaces the imported `1.2.1` sampler. Final generator SHA-256:
`c20bbec95c273fc794b565af52a12702ae1a9ebdc5c11475c0245f3662d6e014`.

## Repair decisions

- Replaced nine partly redundant axes and three bypassing degenerate textures
  with five observable controls: `grid_h`, `grid_w`, `n_pairs`, `palette_kind`,
  and `orientation_family`.
- Every advertised value is constructive in every difficulty band. Unknown
  axes, invalid difficulty values, non-integer seeds, negative/non-integer
  sample indices, and wrongly typed axis values are rejected explicitly.
- Defaults strongly favor the canonical 9×9, 10×10, and 11×11 square profiles
  with two pairs, while exact overrides retain the full 7..13 and 1..4 domains.
- Axis-aligned draws with at least two pairs begin with a crossing horizontal
  and vertical pair; additional pairs are selected by deterministic
  backtracking. Diagonal draws use only perfect diagonals. Placement never
  silently returns fewer pairs.
- `observe_overrides` recovers all five controls from returned pixels;
  `self_check` validates rectangularity, palette, pair counts, geometry, and
  homogeneous orientation family.
- `strict_canonical_like` recognizes square 9..11, two-pair, crossing
  horizontal/vertical instances. Final strict support was 392/600 (65.33%).

## Teaching contract and strongest shortcut

Both canonical demonstrations and the canonical query use color 2 as the
horizontal pair and color 3 as the vertical pair. The strongest retained rival
therefore hard-codes those color roles. It fits all three labeled canonical
pairs but fails the exact generated seed-17/sample-1 swapped-role case in
`counterexamples/fixed_color_roles_swapped.json`; the selected Racket receipt is
under `checks/counterexamples/0eabac67e70a/`.

`SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`,
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable` all bind
that executable rival. Lessons use two demonstrations and one query. The final
100-lessons-per-band census checked 300 production lessons and all 900 query
rotations, with 899 unique inputs and no measured ambiguity, hook warning,
materialization error, or rival-scoring error.

## Verification and retained tools

- Final strict battery: 12/12 stages green in `checks/after-final/`.
- Final portable task tests: 32 passed in `checks/task-tests-final/`.
- Canonical-profile floor: 46/60 exact and 60/60 envelope hits, with exact
  support in every band.
- `workspace/reference_probe.py` is an independent Python translation and
  portable canonical-data loader used only by task-local tests; it is not label
  authority.
- Test-first red/green logs are retained under `checks/tdd/`.

## Provenance, reversals, and limits

No prior return was used as a semantic lead: the task's associated-notes file
was empty and there was no task review index. The retained `b90d4c3d5553`
example was consulted only for shared checker/API patterns, not for task logic.
The previous choice to advertise aliases (`palette_size`,
`n_distinct_colors`) and diagnostic degenerate textures was reversed because
those controls were not independently honored and bypassed other overrides.

Finite declared-rival checks do not prove unique induction against every
possible rule. The sampler intentionally excludes unequal oblique pairs even
though the authority's sign-step implementation has defined behavior for them;
that restriction keeps both endpoints on every emitted span. The post-repair
visible solve is exposure-declared and its masked query remains unscored here.
## Current reviewer considerations

Source SHA-256: `c20bbec95c273fc794b565af52a12702ae1a9ebdc5c11475c0245f3662d6e014`.

# Decisions: 0eabac67e70a

## D1 — Preserve and pin the authority

- **Original choice:** the generator had no `RULE_HASH` pin; the selected and
  canonical authorities nevertheless executed all canonical pairs identically.
- **New choice:** retain the Racket rule byte-for-byte and pin `4a7acff260a8`.
- **Alternative rejected:** editing the rule to enforce only crosses. That would
  change authority to match a narrower title instead of repairing the sampler.
- **Probe/evidence:** baseline/final `rule_smoke` and `authority_sync` receipts.
- **Limit:** the authority defines unequal-oblique sign-step behavior that this
  sampler intentionally does not emit.

## D2 — Replace aliases and degenerate textures with five real controls

- **Original choice:** nine axes included `palette_size` and
  `n_distinct_colors` aliases of `n_pairs`, two single-token metadata axes, and
  textures that returned fixed 9×9 grids before other controls were read.
- **New choice:** expose only `grid_h`, `grid_w`, `n_pairs`, `palette_kind`, and
  `orientation_family`; reject every unknown key.
- **Alternative rejected:** keep the old names and declare thousands of
  incompatibilities. That would document accidental coupling rather than make
  controls independently useful.
- **Probe/evidence:** `checks/tdd/01-unknown-override-red.txt` through
  `04-contract-green.txt`; final override stage in `checks/after-final/`.
- **Failure mode guarded:** typoed axes and mixed overrides can no longer return
  a plausible but uncontrolled grid.

## D3 — Canonical-profile defaults with full exact override domains

- **Original choice:** difficulty-specific draw ranges made declared values
  illegal in some bands and yielded 0/60 exact canonical profiles.
- **New choice:** every band accepts the entire declared domain. Weighted default
  choices favor square 9..11 and two pairs without clamping explicit requests.
- **Alternative rejected:** force every default grid to exactly one canonical
  size. That would pass the floor but unnecessarily collapse input diversity.
- **Probe/evidence:** final profile floor is 46/60 exact and 60/60 envelope;
  task tests exercise the full domain in every band.
- **Limit:** the weighting is curriculum policy, not a claim that canonical
  frequencies represent a natural distribution.

## D4 — Construct geometry; never accept a shortened request

- **Original choice:** each pair had 40 random placement attempts and a failed
  placement silently reduced the realized pair count.
- **New choice:** enumerate legal segments, shuffle deterministically, and use
  backtracking to select non-colliding endpoint pairs. Axis-aligned requests with
  two or more pairs begin with a real crossing pair; diagonal requests use only
  perfect diagonals.
- **Alternative rejected:** raise only after the old retry cap. The cap was an
  avoidable source of seed-dependent failures and did not prove feasibility.
- **Probe/evidence:** corner override cases in task tests, including 7×13 with
  four diagonal pairs and 13×7 with three axis-aligned pairs.
- **Limit:** endpoints may be interior to another pair's output span; this is
  lawful because input colors remain distinct and the authority outputs a union.

## D5 — Use disjoint low/high palettes

- **Original choice:** four palette labels were declared but never read.
- **New choice:** `low={1,2,3,4}` and `high={5,6,7,9}` are disjoint and directly
  recoverable from pixels. Color 8 remains reserved for output.
- **Alternative rejected:** retain four overlapping labels. Overlap makes a
  one-pair grid insufficient to observe which exact control was honored.
- **Probe/evidence:** `observe_overrides` equality assertions across all bands.
- **Limit:** palette family is intentionally coarse; color order still varies.

## D6 — Validate the realized grid, not RNG bookkeeping

- **Original choice:** `self_check` only counted color multiplicities; it accepted
  malformed geometry and two old degenerate textures.
- **New choice:** validate types, rectangular dimensions, allowed colors,
  exactly-two counts, 1..4 pairs, segment length, and homogeneous axis/diagonal
  family. `observe_overrides` independently recovers all five axes.
- **Alternative rejected:** infer compliance from `gen_ctx` draw metadata.
  Returned pixels are the public contract and can diverge from requested draws.
- **Probe/evidence:** mutation/invalid-input task tests and strict self-check stage.

## D7 — Add a source-bound semantic shortcut and lesson contract

- **Original choice:** no strict hook, witnesses, rivals, shortcut, or lesson
  identifiability check existed.
- **New choice:** declare the fixed-color-role shortcut that fits all canonical
  pairs, a generated counterexample witness, and two-demo lesson checks. Defaults
  are scheduled so every three consecutive generated pairs contain enough
  counterevidence for any one-query rotation.
- **Alternative rejected:** use an “interior-only span” rival. Canonical examples
  already refute it, so it does not address the strongest canonical ambiguity.
- **Probe/evidence:** `counterexamples/fixed_color_roles_swapped.json`, final
  semantic gate, and 300-lesson/900-rotation census.
- **Limit:** this proves only the declared rival was refuted in the measured
  population; undeclared hypotheses remain possible.

## D8 — Keep an independent portable oracle and regression suite

- **Original choice:** no task-local tests or reusable probe existed.
- **New choice:** add `workspace/reference_probe.py` using public
  `reviewer_support` helpers and an independent Python authority translation;
  add 32 portable tests. Red/green iterations are retained under `checks/tdd/`.
- **Alternative rejected:** test production helper functions against themselves.
  That would allow one defect to agree with its own test oracle.
- **Probe/evidence:** `checks/task-tests-final/result.json`.
- **Limit:** Racket remains label authority; the Python oracle is regression
  support only.

## 2026-10-24 — Native parametric span-scope adapter

- **Decision:** keep `span_scope="all_pairs"` as the byte-exact canonical default
  (`4a7acff260a86c686966744190dc9d977bc36b50cefaf25d5996fc6642fc5129`)
  and add `span_scope="junction_cluster"` as a separate episode-fixed rule.
- **Alternative semantics:** first compute every same-color endpoint span and
  per-cell coverage; the unique doubly covered cell is the input-dependent
  junction; then retain and paint only spans containing that junction. The
  protected-Racket wrong-junction counterfactual changes the final output on a
  7x7 and a 30x30 case.
- **Teaching choice:** every generated scene has one horizontal/vertical crossing
  pair plus non-crossing distractor spans. The first two demonstrations refute
  fixed-first-demo colors, two-longest, two-shortest, and two-center-nearest
  shortcuts. A finite audit covered seeds 0..11 with 2, 3, and 6 demos.
- **Runtime envelope:** 2..6 demonstrations and exactly four distinct queries;
  query shapes are 7x7, 12x16, 22x26, and 30x30. Public projections expose one
  unanswered query and no private settings, programs, seeds, or future queries.
- **Evidence:** native qualification passed both settings on seeds 0 and 17
  (4 jobs, 40 protected-Racket evaluations), and the changed-ticket suite passed
  61 tests. `workspace/parametric/verify.py` rebuilds the finite teaching and
  public-projection evidence for future reviewers.
- **Limit / next action:** this is bounded reviewer qualification, not universal
  learnability, training admission, or owner acceptance. Integrate the exact
  source and run the owner-side fresh qualification, witness replay, and native
  acceptance path.

