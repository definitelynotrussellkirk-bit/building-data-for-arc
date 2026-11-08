# Working notes: 75837d4fa905

## 2026-10-07 repair review

Baseline `f460dc837723a906659200763467bbe66f7b7e5b340aae2e3f8d27ca3037dea3`
ignored the advertised `n_squares` override, exposed dead/degenerate axes, and
accepted composite non-square inputs such as a solid 3×3 block.  The repaired
v3 generator narrows the public surface to three exact observable axes,
constructs nonconflicting 2×2-square scenes, pins the unchanged canonical rule,
and declares the canonical-fitting `interior_only` rival with an executable
boundary-clipping witness.

A first 300-lesson census found 28 ambiguous query rotations because some
four-pair windows had only one boundary witness.  The final even/odd schedule
places two boundary witnesses in every four-pair window; the rerun found 0
production ambiguities and 0/1,200 ambiguous rotations.  The exact failing
seed/start remains a task-local regression test.

Known scope: ordinary generated scenes reserve complete square-plus-bloom
supports, so shared bloom-target collisions are validator/test support rather
than production-sampler support.  The authoritative rule and validator still
implement first-row-major-writer behavior for such lawful overlaps.
## Current reviewer considerations

Source SHA-256: `e27e0582a89f0f77b9dbb9ca6849c44d349c219a608e0611070bdc94e45db9a4`.

# Decisions for `75837d4fa905`

## D1 — Preserve and pin the canonical authority

**Decision.** Leave the canonical Racket row byte-identical and add
`RULE_HASH = "e56cca9b3b6c"` to the generator.

**Rationale.** Canonical outputs were correct; the defects were in generation,
validation, controls, and teaching support. Rewriting a correct authority would
have expanded risk without repairing the actual failures.

**Alternatives considered.** Replace the Racket scan with a new implementation,
or alter overlap behavior. Both were rejected because rule smoke and authority
sync already established the selected canonical authority.

**Probe/failure mode.** The final rule-smoke stage applied 120 generated inputs
and found 120/120 Python-mirror parity with zero mismatches. Any authority drift,
wrong pin, mutation, or output-shape error would fail the battery.

**Limitation.** The Python mirror is diagnostic only; Racket remains authoritative.

## D2 — Replace the nominal nine-axis surface with three exact controls

| Input choice | Baseline/original rationale | Final choice | Alternatives and failure modes | Evidence |
|---|---|---|---|---|
| `grid_h` | Advertised 5–16; actual difficulty branches used narrower ranges. Original rationale unknown. | Exact 7–16. | Retaining 5–6 would make the full `n_squares=4` boundary matrix harder to guarantee and has no canonical support. Values are type/range checked rather than clamped. | `checks/after/checks/75837d4fa905_after_override_results.json` |
| `grid_w` | Advertised 5–18; actual branches used narrower ranges. Original rationale unknown. | Exact 8–18. | Retaining 5–7 would conflict with the total four-corner fallback at maximum square count. Silent clipping/clamping was rejected because it breaks exact-control semantics. | same |
| `n_squares` | Advertised 1–8, but implementation drew a different key, `square_count`, so the override was inert. Original wide-range rationale unknown. | Exact 2–4. | One square was rejected as an under-informative/minimal teaching grammar; 5–8 would require compatibility rules with dimensions and exceed useful canonical support. | `checks/red-task-tests/result.json`; `checks/task-tests/result.json` |
| colors | Baseline had `palette_kind`, `palette_size`, and `n_distinct_colors`, but these did not form a coherent exact surface. | Draw `n_squares` distinct colors from 1–9; background fixed at 0. | Keeping palette aliases would preserve dead or ambiguous controls. Color roles are interchangeable for this rule, so no public palette axis was needed. | final lint/override stages |
| placement | Baseline exposed fixed/dead position and density axes and kept all ordinary squares interior. | Internal randomized constructive placement; not a public override. | Rejection-only placement could fail at legal boundaries; unconstrained placement could create composite/non-background targets. A deterministic corner fallback makes every advertised combination total. | task tests and override stage |
| texture/degenerates | `no_squares`, `single_cell`, and `on_edge` were mixed into an advertised ordinary axis. | Remove the texture axis. Boundary squares become normal production cases; missing/malformed sources are rejected. | Metadata bypasses were rejected because they make invalid inputs appear lawful and confuse downstream exact-control checks. | final defect lint |

All scheduled constants pass through keyed `gen_ctx` draw calls. A prior
iteration assigned canonical profile values directly; the override/provenance
checker correctly rejected that, so the final implementation uses singleton
`draw_choice` calls for scheduled profile values.

## D3 — Use canonical profile scheduling without making profile a public axis

**Decision.** Cycle through the four canonical `(height, width, square-count)`
profiles during four of every six sample indices, then use difficulty-specific
free draws for the other two.

**Rationale.** This guarantees exact canonical-size/palette support in every band
while retaining noncanonical variation. Palette size is implied by distinct
square count plus background.

**Alternatives considered.** Randomly hope to hit canonical profiles, which had
insufficient profile-floor support; or make `profile` another public axis, which
would duplicate the three exact controls and introduce compatibility questions.

**Probe/failure mode.** The final profile-floor report observed exact support in
all bands (15/20 easy, 16/20 medium, 15/20 hard) and accepted 4/4 canonical
inputs. `strict_canonical_like` makes profile drift executable.

**Limitation.** This reproduces canonical dimensions and palette cardinality,
not every canonical spatial arrangement.

## D4 — Make the teaching grammar strict and constructive

**Decision.** A lawful teaching input has two to four distinct-color solid 2×2
squares; every in-bounds diagonal target is zero in the input. Generated sources
reserve their complete in-bounds source-plus-target supports.

**Rationale.** Grouping by color gives an unambiguous source parse and rejects the
baseline's 3×3 composite hole. Constructive support reservation avoids retries,
source/target conflicts, and accidental extra 2×2 detections.

**Alternatives considered.** Scan every 2×2 window in arbitrary composites, or
accept singleton lessons. Both broadened the validator beyond the documented
teaching domain and weakened task semantics.

**Probe/failure mode.** Tests reject solid 3×3 composites and one-square inputs,
accept canonical inputs, and exercise every axis boundary. The generator calls
`self_check` before returning.

**Limitation.** Ordinary generation does not create shared bloom targets. The
validator and rule mirror deliberately accept/test a lawful two-square overlap,
where first row-major writer wins.

## D5 — Promote clipped boundaries from a degenerate to required evidence

**Decision.** Declare `interior_only` as the strongest canonical-fitting rival and
`clipped_boundary_bloom` as its witness. Even sample indices use edge mode; odd
indices use interior mode.

**Rationale.** All four canonical pairs are interior, so they cannot distinguish
“clip out-of-bounds targets” from “skip any boundary source.” A clipped source
with at least one surviving in-bounds corner is the smallest direct witness.

**Alternatives considered.** Keep boundaries random, use one boundary witness per
four-pair window, or waive the ambiguity. The first two failed query rotation;
the waiver would leave a known teaching defect.

**Probe/failure mode.** The exact witness is Racket-bound in
`checks/shortcut-witness/witness.json`. The semantic gate observed witness hits in
298/600 draws and 60/60 checked disagreements with the rival.

## D6 — Guarantee two witnesses in every four-pair lesson

**Decision.** Production lesson windows are four consecutive samples with three
demonstrations and one query. Alternating edge/interior samples guarantees two
boundary witnesses in every window, so holding out any one pair still leaves at
least one witness among the demonstrations.

**Rationale.** The first 300-lesson census found 0 production ambiguities but
28/1,200 ambiguous rotations. One witness per window is sufficient only when its
position is never queried.

**Alternatives considered.** Ordered-only lessons or resampling ambiguous
rotations. Ordered-only would encode a brittle downstream assumption; resampling
would obscure deterministic failures and complicate replay.

**Probe/failure mode.** The exact formerly failing seed `3999318746`, start 28 is
retained in `test_four_pair_lesson_is_identifiable_under_every_query_rotation`.
The final 300-lesson census found 0/1,200 ambiguous rotations.

**Limitation.** This proves the deterministic consecutive-window schedule against
the declared rival over the tested census, not all possible adversarial rivals or
nonconsecutive downstream assembly.

## D7 — Preserve first-writer semantics without forcing collisions into production

**Decision.** Analyze squares from the original input, scan sources in row-major
order, and paint only cells still zero in the evolving output. Permit shared
bloom targets in validation and tests, but reserve disjoint supports in default
generation.

**Rationale.** This matches the canonical `for*/fold`/`for/fold` behavior while
keeping generated examples simple and reliably constructible.

**Alternatives considered.** Last-writer wins, simultaneous overwrite, or reject
all overlaps in the validator. Those would either diverge from authority or make
the validator narrower than the rule.

**Probe/failure mode.** A lawful overlap test checks that color 3, the earlier
source, owns the shared cells. Rule-smoke mirror parity would expose divergence.

**Limitation.** Overlap precedence is validator/test support, not generated lesson
support; therefore no curriculum-composition claim is made for sequential state.

## D8 — Retain failures and use portable selected-task tests

**Decision.** Add tests only under the selected task's `tests/` directory and use
`reviewer_support.find_root`/`canonical_pairs` so they run in the portable task-test
snapshot.

**Rationale.** Direct source-tree pytest cannot import numeric task modules in the
same layout as the isolated checker. The official `task_tests` stage is the
portable contract and records copied source hashes.

**Alternatives considered.** Patch the frozen root fixture or depend on fixed
`parents[...]` paths. Both were explicitly disallowed/brittle.

**Probe/failure mode.** Retained red runs show 19/20, 2/20, and 1/21 failures at
the appropriate TDD stages; final and fresh-replay runs both pass 21/21.

## D9 — Correct task-local documentation

**Decision.** Update `SUMMARY.md` to v3 behavior and record the repair/census in
`notes.md`.

**Rationale.** Leaving the old “2–6 isolated interior squares, v2.0.1” description
would reintroduce a misleading contract even though code and tests were correct.

**Probe/failure mode.** The four changed files are hash-compared after applying the
exact patch to a fresh packet; all bytes match in
`checks/fresh-replay/verification.json`.
