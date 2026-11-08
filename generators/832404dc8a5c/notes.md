# Current notes: 832404dc8a5c / d2acf2cb

## Selected v4 behavior and authority

The selected generator is **4.0.0**, source SHA-256
`d1b17ce79331a3490635b917a3c3d1d349d0865e9f7f1657ef84897de48d8634`.
The canonical Racket semantics are unchanged: a row is selected when both edge
endpoints are 4, and a column is selected by the equivalent top/bottom pair.
Apply `0 ↔ 8` and `6 ↔ 7` once to the union of selected lanes. Anchors and cells
outside that union stay unchanged; an intersection receives one swap.

Labels continue to come from the canonical Racket authority, declared rule hash
`bce3d4596195`, exact program-text SHA-256
`5e8bc7939bbc421cafb04acc3034fae164476344c7aa36f1f9e6cf584171343d`.
Selected-authority text synchronization at `/racket_target/target_code` is
formatting-only and preserves the executed semantics and the canonical program
above. Imported associated notes remain in
`evidence/associated_notes.jsonl` as provenance.

## Repair decision and retained intersection regression

Independently drawing orientation and lane palette made some v3 lessons
ambiguous even when every individual label was correct. The repair couples
semantic examples into a teaching schedule while retaining randomized lane
positions, field texture, counts and dimensions within each scheduled profile.
It also validates controls strictly and broadens the lawful size range.

All four canonical pairs have only rows or only columns, so none contains a
row/column intersection. A rival that swaps rows and then columns therefore
matches **4/4** canonical labels: its erroneous second swap has nowhere to act.
The actually recorded hard seed-28 baseline lesson likewise has three
intersection-free demonstrations. Its mixed query exposes the rival at
zero-based `(6, 9)`: input 8 must become 0, but two swaps return 8.

The task-local [intersection witness](counterexamples/double_swap_intersection_seed28.json)
projects that recorded query to **6 × 8**, the minimum canvas in this family's
declared domain, preserving both endpoint pairs and dense field texture. The
same discrepancy is now at `(3, 6)`. It records the original retained row/column
indices, baseline source hash, original failure-file hash, exact reference and
rival Racket, and both executed outputs. Fresh Racket execution reproduces all
three baseline demo matches, the original query mismatch, the projected mismatch,
and all four canonical matches. This is an adapted regression witness, not a
claim that the reduced grid itself was emitted by seed 28. Its source evidence
is `checks/teaching-before/hard__production__sequential_double_swap__first_failure.json`
in the review workspace; the baseline generator hash is
`cc3d5237e716646abfd0c114e6b2dbb504f377903fc8ca4b8f62dfd73b420a73`.

## Input grammar and strict authoring controls

Lawful inputs have 6–30 rows and 8–30 columns and integer cells from
`{0, 4, 6, 7, 8}`. Color 4 occurs only in complete endpoint pairs of interior
lanes, never as a corner or lone marker. Values 7/8 occur only inside anchored
lanes; the field outside lanes uses 0/6. Outputs retain the input dimensions.

`seed` must be an integer and `sample_index` a nonnegative integer; booleans are
not integers for this contract. Difficulty is `easy`, `medium`, `hard`, or `None`.
Unknown override names, invalid enums, coerced numeric strings, fractional integer
controls, booleans, nonfinite densities and out-of-range values are rejected.

| Control | Accepted values |
|---|---|
| `grid_h`, `grid_w` | Exact integers 6–30 and 8–30 respectively |
| `n_anchored_rows`, `n_anchored_cols` | Exact integers 0–4 |
| `zero_density` | Finite numeric value 0.1–0.7; a draw parameter, not a per-grid exact fraction |
| `lane_palette` | `mixed`, `swapped`, `base` |
| `texture` | `none`, `no_anchors`, `all_anchored`, `single_anchor` |

`None` leaves a control unspecified. Explicit lane counts are recorded as realized
counts. A simultaneous zero row/column count is rejected; use the explicit
`no_anchors` texture instead. Degenerate textures are override-only lawful
controls and reject lane-count overrides. `no_anchors` additionally rejects a
lane-palette override and requires both 0 and 6 at a minimum of
`max(6, ceil(height × width / 10))` cells each. Sparse or monochrome lane-free
identity grids are outside this grammar. `all_anchored` and `single_anchor`
retain their declared fixed layouts. These controls are outside the default
teaching guarantee.

## Default lesson and size schedules

The semantic profile depends on `sample_index mod 4`:

| Phase | Anchor layout | Lane palette |
|---|---|---|
| 0 | Rows only | Base: 0/6 |
| 1 | Rows and columns | Swapped: 7/8 |
| 2 | Columns only | Swapped: 7/8 |
| 3 | Rows and columns | Base: 0/6 |

Lane painting places both values of the selected palette at randomized lane
positions. The input's marker geometry determines the selected lanes; the size
schedule does not determine output colors. Difficulty controls lane complexity
without removing the four semantic profiles.

The five-slot size cycle uses three canonical-sized slots, one long rectangle,
and one 30 × 30 grid. Over a full cycle this is **60% / 20% / 20%**:

- Canonical-sized: width 9; height 9 for swapped lanes, or a draw from 6, 7 and
  10 for base lanes. This is a size claim: mixed orientations and some hard-band
  lane counts deliberately extend beyond the original canonical examples.
- Long rectangle: 21–29 rows by 8–20 columns, or 6–20 rows by 21–29 columns.
- Maximum-size: 30 rows by 30 columns.

The semantic and size periods are coprime. Their combined contract is
`LESSON_SCHEDULE_PERIOD = 20`, covering **4 semantic profiles × 5 size slots**.
These are exact scheduled proportions over complete cycles, with randomness
inside the buckets. Explicit dimension, palette, count, density or texture
overrides are authoring requests and are excluded from these default-distribution
and lesson claims.

The intended default lesson is **three demonstrations plus one query at four
consecutive sample indices**. Any three of those four profiles expose both
orientations, both palette directions, and a mixed intersection. Thus the
teaching contract supports the ordered first-three/fourth-query export and
each of the **four query-slot rotations** of the same bundle. A query-slot
rotation holds out a different pair; it is not a spatial grid rotation.

This guarantee is scoped to the seven declared rivals: `identity`,
`swap_everywhere`, `rows_only`, `columns_only`, `forward_only`, `reverse_only`,
and `double_swap_intersections` (the baseline audit's `sequential_double_swap`).
Aliases across declaration hooks do not add new rivals. It does not assert
unique inference against arbitrary programs, fewer than three demonstrations,
nonconsecutive sample sets, or overridden lessons.

Current source-bound review evidence (paths relative to the review workspace):

- `checks/schedule-census.summary.json`, with the complete report losslessly
  retained as `checks/schedule-census.json.gz`: all 20 start residues at seed 0
  in each of three bands; **60 lessons, 240 query-slot rotations**, zero
  ambiguity, materialization or scoring errors. The consecutive windows overlap
  and contain **50 unique inputs**. This exhausts that declared period at the
  stated seed, not all seeds.
- `checks/lesson-census.summary.json`, with the complete report losslessly
  retained as `checks/lesson-census.json.gz`: **300 lessons, 1,200 labeled pairs,
  1,200 unique inputs and 1,200 query-slot rotations**; zero ambiguity,
  materialization or scoring errors. Both production and rotation verdicts are
  `no_ambiguity_found` within the finite audited rival space.

## Proposed parametric extension — separate from canonical approval

The [task-local prototype](workspace/parametric/README.md) proposes
`direction_scope ∈ {union, rows, columns}`. `union` preserves the original rule;
the alternatives restrict which anchored orientation receives the same swaps.
The hidden setting is chosen once from an episode seed and held fixed across
all demonstrations and queries. Explicit parameter overrides are recorded
separately as authoring controls. Every label and rival prediction executes the
exact materialized Racket program. Public challenges contain only demonstration
pairs and query inputs; parameters, programs and query answers remain private.

`checks/parametric/artifacts-final/report.json` records **nine complete episodes**
with 27 demonstrations and nine queries, including three ordinary seed-selected
episodes covering all settings. It records **152 Racket grid evaluations**, all
81 parameter-rival demonstration checks, zero ambiguous episodes among the three
settings, all four canonical/default matches and twelve generated default-rule
comparisons. The shared lawful witness distinguishes all three pairs of settings.
The 21 focused prototype tests pass, and
`checks/parametric/artifact-verification.json` verifies the saved public schemas,
exact source/program hashes and private provenance.

This extension remains **prototype / proposed, not approved**. Its fixed
demonstration schedule and smaller 6–13 by 8–12 episode-sampling envelope are
bounded authoring evidence. The separate 30 × 30 test checks its Racket rule
domain. Canonical repair acceptance does not approve these alternative rules or
establish training admission.

## Current owner source and evidence limits

Selected review-02526caab8ea05c1 repair4.0.0:strict controls,explicit incompatible combinations and dense lawful edge fixtures;four-profile teaching cadence covers directions,palettes and intersections. Canonical Racket unchanged;selected target formatting synchronized only,archival raw_code retained. Reviewer12/12 battery,121 portable/fresh tests,eight changed paths exact. Production3003-demo lessons/1200 rotations clean against seven unique rivals;all20 starts at seed0 across3 bands60 overlapping windows/240 rotations/50 unique inputs. direction_scope union/rows/columns prototype has nine Racket-backed episodes with content-derived public IDs;canonical-default behavior checked,not claimed byte-identical unless actual evidence establishes it. Competing review-bf76c6f3e46f8419 generator/endpoint-threshold family retained unselected;no merging of independently reviewed bytes. No production parameter API,variant approval,training admission or owner repair battery rerun.

Unselected competing same-baseline repair,not a current-source approval. Select review-02526caab8ea05c1 with121 portable/fresh tests and12/12 strict battery. Preserve this distinct endpoint_threshold family and48-test/11-of12 battery evidence;its exact finite-set object_count warning remains failed. Its alternate generator450d238a differs from selectedd1b17ce7;do not combine their source bytes,claim its reported tests cover selected source,replace the direction_scope family or increment current prototype count. Proposed two settings have canonical4/4 default parity and8/8 parameter rotations;finite-only,unapproved. Audits from both returns remain actionable. Retained at `workspace/proposals/review-bf76c6f3e46f8419/manifest.json`.
## Current reviewer considerations

Source SHA-256: `d1b17ce79331a3490635b917a3c3d1d349d0865e9f7f1657ef84897de48d8634`.

# Decisions — review-02526caab8ea05c1

## Preserve the canonical rule; repair its teaching distribution

The rule selects a cell when its row has 4 at both horizontal endpoints or its column has 4 at both vertical endpoints. On that union it exchanges 0↔8 and 6↔7 once; all other values and cells remain unchanged. A row-column intersection is selected once. This exact canonical program remains authoritative, with rule hash `bce3d4596195` and source SHA256 `5e8bc7939bbc421cafb04acc3034fae164476344c7aa36f1f9e6cf584171343d`.

The central problem M1 was lesson composition. Individual examples could be lawful and correctly labeled while leaving a wrong rule consistent with all demonstrations. The baseline seeds 0..59 in three bands produced 41/180 consequentially ambiguous ordered lessons against seven simple rivals. A particularly useful rival swaps rows and then columns: it agrees with all four original canonical pairs but incorrectly swaps intersections twice. `checks/teaching-before/` retains exact examples, outputs, seeds, accepted indices, and the scoring code.

I rejected leaving lane orientation and palette independent in each example, because more samples alone do not ensure each short lesson teaches the rule. I also rejected merely adding one mixed example to every four-pair window: if that example becomes the query, its intersection witness disappears from the demonstrations. The default semantic cycle is now rows/base, mixed/swapped, columns/swapped, mixed/base. Any three consecutive profiles from the four-cycle contain a mixed example and both palettes. Each selected lane contains both relevant palette colors; preserved field cells reject indiscriminate swapping. These are visible input witnesses, not hidden metadata supplied to a learner.

The finite contract names identity, swap-everywhere, rows-only, columns-only, forward-only, reverse-only, and double-swap-intersections. It uses actual input/output behavior, and a failure means a rival fits every demonstration while disagreeing with the query. Rivals agreeing with the intended query are not false failures. Three demonstrations plus one query is the measured production assembly. All four held-out-query choices are supported by the default schedule and tested; there is no claim for arbitrary custom mixtures or every possible rival program.

## Make size variation substantive and retain canonical anchors

The semantic cycle is combined with a five-phase size cycle, giving a declared period of 20. Three phases use canonical-sized grids (width 9, base height in 6/7/10 or swapped height 9), one uses a long rectangle with longest side 21..29, and one uses 30×30. The resulting category mix is 60% canonical-sized, 20% long rectangles, and 20% 30×30, so 40% have longest side greater than 20. Canonical-sized does not mean every mixed or four-lane example belongs to `strict_canonical_like`.

This intentionally keeps more canonical size anchors than an aggregate 60%-large curriculum recommendation would. That recommendation is not imposed as a universal per-task quota: this task benefits from retaining the small-grid visual grammar while still exercising long lanes and full-size fields. The added dimensions contain dense background/palette structure and extended semantic lanes. They are not blank padding. A uniform arbitrary-size sampler was rejected because it would blur the anchor/extension allocation and complicate complete schedule coverage without improving the selected rule witness.

I checked the possible shortcut introduced by a deterministic schedule: all interpretation remains recoverable from visible paired endpoints and palette values, and each default demonstration subset refutes all seven declared rivals without access to sample index. The independent review found no blocking new shortcut; the stated limitation is the finite rival inventory and bounded seeds, not an assertion of unrestricted uniqueness.

## Strict overrides and an explicit lawful boundary

M2 includes silent coercion and undeclared combinations. Integer controls now require integers, excluding booleans; seed may be any integer, while sample index must be nonnegative. Difficulty and enums must be declared values, dimensions are bounded at height 6..30 and width 8..30, density must be finite and in range, and unknown controls are rejected even if their value is None. Advertised exact lane counts fit the smallest allowed interior. Invalid combinations fail explicitly rather than silently changing the user's requested plan.

`no_anchors`, `all_anchored`, and `single_anchor` are declared lawful degenerate textures. They are diagnostic controls, not default lesson slots. The no-anchor identity case still requires a dense field: each of 0 and 6 occurs at least `max(6, ceil(height*width/10))` times. This preserves the task's material grammar and prevents a sparse/constant impostor from passing merely because the Racket function can return it unchanged. The sampler enforces that density for the explicit no-anchor override. The validator additionally rejects ragged, noninteger, out-of-palette, or malformed-anchor grids.

The strongest alternative was making all overrides inherit the teaching schedule. That would undermine their purpose as exact diagnostic controls. Their lawfulness is checked separately; the default rotation guarantee is explicitly excluded when controls replace its schedule.

## Synchronize only the selected authority representation

M3 was exact formatting drift between the canonical program and the selected JSON `racket_target.target_code`. The official proposal checked identical tokens in its restricted Racket reader subset and changed only that string. The baseline authority execution parity already passed; the after battery confirms exact selected synchronization and execution parity. Canonical ledger SHA256 `9d46eb627dac0d3f096b8b1a63dd95e012039cf72d0d08f3d1bbbc109211965f` is unchanged, as is archival `raw_code`. I rejected rewriting archival code or the canonical program merely to satisfy formatting checks.

## A small, explicit parametric extension

Before the canonical repair, the task-local prototype was implemented for a single meaningful axis: `direction_scope = union | rows | columns`. It changes the Racket selection predicate, rather than only the Python input distribution. The chosen scope is sampled once per seeded episode or explicitly overridden once, and the same materialized program labels every demonstration and query. Inputs use a scope-independent random stream. The three-demo sequence is rows/swapped, columns/base, mixed/swapped; the query is mixed/base.

Public exports contain only task grids and demonstration labels. Scope, materialized source, hashes, authoring query labels, and selection provenance remain separate. An early provenance test exposed missing distinction between seeded and explicit selection; six real failures are retained and the final path records one selection through either bridge ownership path. Final evidence evaluates nine episodes and all three rival programs on the demonstrations, with no ambiguous episode. The canonical default agrees with actual Racket on four canonical and 12 generated inputs.

I rejected introducing independent palette, lane, and direction parameters together: that would multiply unidentifiable short lessons and weaken the evidence for each axis. The retained extension is proposed and bounded, with its own 21 tests and exact program hashes. Canonical repair acceptance does not approve noncanonical variants for training.

## Evidence, audits, and completion policy

The required before/after battery and explicit portable task-test run were executed, and the final strict battery reused a source-bound fixed-seed complete schedule census. A second census used 100 hashed-seed lessons per band with all query positions. The fixed-seed census has 50 unique inputs across 60 overlapping lesson windows; the larger census has 1,200 unique inputs. These denominators are kept distinct. Fifteen declaration bindings are aliases for seven rival functions, not fifteen independent hypotheses.

The two immutable audit draws were inspected without edits. A1 confirms an existing ordered-versus-rotated teaching issue, with the target hook correctly rejecting the rotated failures. A2 confirms an existing morphology/parity correlation and a lawful override recombination missed by its rival inventory; the offending query is not emitted by that target's default schedule. `AUDIT.md` states the exact public-Racket checks and limits. Neither finding was silently folded into the main repair.

The blind solve ran before rule exposure; the final repair solve honestly declares earlier exposure and is bound to the final generator bytes. Both retained one actual attempt and matched three visible examples. Their hidden query correctness remains unknown. The work logs are authored records, not captured token-level model traces.

The original packet's first full extraction actually failed with ENOSPC. A manifest-verified subset allowed review work to proceed; the optional helper later restored all missing originals using read-only hardlinks only among fresh identical reference files. This preserves the official packager's full-inventory gate and existing edited bytes. The helper's first integration serialization failure and its successful regression test remain in evidence. Large reports are losslessly compressed with exact original path/size/hash mappings, and no failure was discarded to meet the return budget. Fresh replay uses the original packet's declared runtime closure, not a claim of another full extraction.

Final replay verified all eight changed paths from a 333-file declared dependency closure and reran all 121 focused tests successfully in a fresh Python environment and offline Racket installation. The exact tested source patch hash is `f132220d94bd3800cc4476005326ace202a1459cca32eb9a5b2e72c531bceba3`. Final handoff additions contain only evidence and review documents. Supported authority-sync commands also created transient repository metadata rejected by the first package attempt; those bytes were preserved under checks rather than weakening the source gate. The expanded-size failure and successful compression preparation are retained as separate package attempts.
