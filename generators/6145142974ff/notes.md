# Working notes: 6145142974ff

## Prior evidence used

`evidence/associated_notes.jsonl` was empty, so no prior return was used as a substantive lead. The immutable selected baseline, canonical ledger row, retained passing example `b90d4c3d5553`, and the packet's battery reports were the evidence sources.

## Baseline findings

The selected baseline generated only matching green components. Consequently, three plausible canonical shortcuts survived: recolor every green component, select every green component with the template's cell count, and use the numerically largest marker color. The generator also swallowed unknown overrides, did not honor advertised grid dimensions, lacked a literal `RULE_HASH`, and described the output incorrectly as preserving the input scene. The before battery recorded 3 blocking failures (`lint`, `defect_lint`, `override`) and 2 advisory stages.

## Repair

Version 3.0.0 pins `RULE_HASH = "d5061c3b9df5"`, follows the canonical blank-output semantics, and constructively places a recognized color-1 template, one or two exact color-3 matches, one or two nonmatches, and isolated majority-key markers. Every ordinary draw includes a same-area wrong-shape distractor. Exact controls cover grid size, shape, match count, distractor count, majority color/count, and number of marker colors; unknown or malformed controls fail loudly.

A three-slot schedule supplies one-match, two-match, and two-distractor cases. Low-key slots include a singleton color 9 so “choose largest color” fails, while the two-match slot defeats “first match only.” Task-local tests use `workspace/probe_support.py` as an independent component analyzer/oracle and check canonical support, controls, malformed inputs, semantic witnesses, and four named rivals.

## Verification and limits

The final generator SHA-256 is `74f509e69fc179963d3295401f9f81b4d9db6c60760a0cb0837724350751a012`. All 12 after-battery stages and 36 task tests passed. A source-bound census materialized 100 lessons per band: 300 lessons, 1,200 unique inputs, zero declared-rival ambiguities, and every named canonical shortcut refuted in every lesson. This finite declared-rival census does not prove universal identifiability, and its production sampler does not rotate each pair through the query position. No canonical or Racket authority source changed.
## Current reviewer considerations

Source SHA-256: `74f509e69fc179963d3295401f9f81b4d9db6c60760a0cb0837724350751a012`.

# Decisions for 6145142974ff

## D1 — Treat the canonical ledger as the semantic authority

**Choice.** Implement the canonical behavior literally: begin with an all-zero output, copy only exact color-3 shape matches, and recolor them with the selected marker color.

**Rationale.** The baseline prose said template, nonmatches, and singleton keys remained, but every canonical output removes them. Rule smoke and the selected Racket authority agree on blank-output semantics.

**Alternatives rejected.** Mutating a copy of the input; retaining nonmatching objects; preserving markers; editing the Racket source to match the old summary. Those alternatives would contradict all canonical outputs.

**Probe.** Canonical support tests compare the independent Python oracle against all four usable canonical pairs; final `rule_smoke` and `authority_sync` are green.

**Failure mode/limit.** The Python mirror is supplemental. Racket remains the sole authoritative output source.

## D2 — Pin the exact authority hash without changing it

**Choice.** Add literal `RULE_HASH = "d5061c3b9df5"` and leave canonical/Racket data untouched.

**Rationale.** The before linter correctly treated the missing pin as blocking. The selected authority already passed execution parity.

**Alternatives rejected.** Deriving the hash dynamically, copying the divergent archival bank source, or patching canonical data. A literal pin is auditable and avoids widening scope.

**Probe.** Final lint, rule smoke, Racket lint, and authority sync all pass.

**Failure mode/limit.** Authority sync still reports an archival divergent copy outside the selected execution source; no change was justified or allowed here.

## D3 — Use a constructive six-slot layout

**Choice.** Place the template and up to four green components in shuffled coarse slots, with markers in a separate bottom key row.

**Rationale.** Exact controls must work at the minimum `10×12` grid without rejection walls. Constructive slots make every advertised Cartesian combination reliable and keep components 4-disconnected.

**Alternatives rejected.** Random placement with retries; large minimum grids; declaring numerous incompatible override combinations. Those approaches either caused the baseline's rejection failures or narrowed support unnecessarily.

**Probe.** Boundary-control tests exercise `10×12` and `16×18` across every shape/count axis in all bands; the override stage passes with unknown-key verdict `rejected`.

**Failure mode/limit.** Six coarse regions are a visible spatial regularity. Slot order is shuffled and does not encode semantic role, but arbitrary dense placement is not represented.

## D4 — Eight literal translation-only template shapes

**Choice.** Support `l3`, `corner3`, `t4`, vertical/horizontal S, square4, long-L5, and zigzag5.

**Rationale.** The canonical rule compares normalized coordinate sets without rotation/reflection. The library covers several sizes, symmetries, concavities, and orientations while remaining fully inspectable.

**Alternatives rejected.** Procedurally enumerating every polyomino; allowing rotations as matches; using only canonical shapes. The first adds needless surface area, the second changes the task, and the third is too narrow.

**Probe.** Exact shape overrides round-trip through `observe_overrides`; task tests compare normalized components against an independent analyzer.

**Failure mode/limit.** The finite library cannot establish behavior on every possible polyomino, though `self_check` intentionally defines the generated domain around these recognized shapes.

## D5 — Generate one or two matches and one or two nonmatches

**Choice.** Ordinary scenes contain `n_matches ∈ {1,2}` and `n_distractors ∈ {1,2}`.

**Rationale.** The baseline's all-match distribution made the strongest canonical shortcut indistinguishable. Two-match scenes also test plural selection.

**Alternatives rejected.** Zero-match examples; three or more candidates; keeping one match only. Zero-match scenes weaken positive grounding, larger counts crowd minimum grids, and one-match-only lessons permit first-match heuristics.

**Probe.** Counts are exact axes, observed after generation, and tested at both values. The census refutes `first_match_only` in all 300 lessons.

**Failure mode/limit.** The curriculum does not exercise zero-match queries.

## D6 — Require an equal-area wrong-shape distractor

**Choice.** The first distractor always has exactly the template's cell count but a different normalized shape; a possible second distractor has a different size.

**Rationale.** This directly refutes the plausible “select by area” shortcut that fits every canonical pair.

**Alternatives rejected.** Only smaller distractors; color-only decoys; disconnected noise. None makes exact shape equality necessary.

**Probe.** `same_size_wrong_shape` is an executable witness, task tests verify it, and `same_cell_count` is refuted in every census lesson.

**Failure mode/limit.** The equal-area distractor comes from a fixed mapping, so it does not cover every wrong shape of that area.

## D7 — Use a strict frequency key, not numeric order

**Choice.** Emit two or three singleton marker colors; one appears two or three times and every other color once. Low-key lessons include a singleton 9.

**Rationale.** Canonical examples happen to use a majority color that is also numerically largest. A lower repeated color plus singleton 9 distinguishes frequency from value.

**Alternatives rejected.** Tied marker counts; arbitrary marker components; always using 9; using only two total markers. Ties invoke an authority tie-break but obscure the intended majority concept, while connected marker blobs confound frequency with area.

**Probe.** Exact majority axes are tested; isolated-component validation is strict; `largest_marker_color` is refuted in all census lessons.

**Failure mode/limit.** Although the authority has a larger-color tie-break, generated lessons deliberately avoid ties.

## D8 — Three-example deterministic curriculum

**Choice.** Cycle through `single_match_low_key`, `double_match_low_key`, and `two_distractors_high_key`; set `EXAMPLES_NEEDED = 3`.

**Rationale.** Every consecutive three examples jointly expose nonmatches, same-area decoys, multiple matches, and frequency-vs-maximum color choice.

**Alternatives rejected.** Independent random profile draws; five-example lessons; exact replay of canonical examples. Random draws can miss branches, five examples cost more than needed, and canonical replay preserves canonical shortcuts.

**Probe.** Task tests check every cyclic start. The 100-per-band census covers all start residues and reports zero declared-rival ambiguity.

**Failure mode/limit.** The production census does not rotate every materialized pair into the query position; cyclic starts are tested locally, not every query rotation.

## D9 — Preserve canonical density without copying canonical grids

**Choice.** Every fifth default sample uses `11×13` and majority color 5; other dimensions and palettes remain banded.

**Rationale.** This guarantees at least one canonical-size/palette profile in each 20-draw band while retaining structural diversity.

**Alternatives rejected.** Hard-code a canonical example; rely on chance; force every sample to canonical dimensions. The chosen approach meets profile-floor requirements without memorizing a full puzzle.

**Probe.** Final `profile_floor` passes in all bands; diversity and distribution gates remain green.

**Failure mode/limit.** The periodic density anchor is detectable, but semantic roles and object geometry still vary.

## D10 — Fail closed on controls and malformed scenes

**Choice.** Validate axis names, exact Python types, integer ranges, enumerations, component counts, recognized templates, singleton isolation, and strict marker majority.

**Rationale.** The baseline silently accepted unknown keys and often ignored requested dimensions, making experiments irreproducible.

**Alternatives rejected.** Best-effort coercion; silent fallback; broad incompatible-combination tables. Explicit errors are more useful to reviewers and samplers.

**Probe.** Unknown/bad overrides fail in tests; every advertised boundary combination succeeds; malformed grids fail closed.

**Failure mode/limit.** `strict_canonical_like` intentionally accepts canonical zero-distractor cases, while ordinary generation is stricter and always supplies distractors.

## D11 — Keep semantic probes reusable and independent

**Choice.** Add `workspace/probe_support.py` with independent connected-component parsing, canonical loading, a pure oracle, and rival solvers.

**Rationale.** Tests should not merely restate generator internals. The helper also gives future reviewers a small probe surface instead of requiring them to rediscover canonical parsing and rival logic.

**Alternatives rejected.** Testing only `rule_mirror`; importing private runner functions; embedding all helpers in one large test file.

**Probe.** The retained red run failed for the intended missing capabilities; the same 36 tests pass after implementation.

**Failure mode/limit.** Independent code can still share conceptual assumptions with production. Racket-backed battery stages remain the external check.

## Review 2026-10-25 — native parametric bridge family

**Decision.** Preserve the exact canonical program as `finish=canonical` and add `finish=bridge_matches`: Stage A keeps only exact color-3 copies of the color-1 template and recolors them with the strict-majority marker; Stage B rediscovers those components in the Stage-A intermediate and joins consecutive components in reading order with deterministic horizontal-then-vertical bridges.

**Why this variant.** The second action consumes an input-dependent intermediate rather than a cosmetic parameter. Replacing only Stage A with an all-green selector changes the bridge endpoints and the final label; the qualified witness changes 24 final cells.

**Sampling/public contract.** The task-local adapter supports 2–6 demonstrations and 1–4 prefix-stable queries, uses identical inputs for both settings, supplies four distinct private queries, masks query labels in public turns, and includes a 30×30 case with six exact matches plus five equal-area distractors.

**Evidence.** The final task suite passes 95 tests. The bounded structural audit covers 320 episodes, 2,560 visible pairs, 320 finite-rival certificates, all demo-count boundaries, matched-input and prefix checks, and 320 stress checks. The protected-Racket audit executes 92 selected labels, six wrong-intermediate scans, and one direct causal replay. Native qualification covers two settings × seeds 0 and 17 (40 labels), and the source-bound witness is independently replayed.

**Bindings.** Production generator SHA-256 remains `74f509e69fc179963d3295401f9f81b4d9db6c60760a0cb0837724350751a012`; canonical program SHA-256 remains `d5061c3b9df5b82102e0f236707adb449060773cb62b2ffa128a4045a210a6be`; manifest SHA-256 is `8512896dc000564e65dc185b45f583fda82c089c49ed56eda814743fa2b25ff6`.

**Limit.** Rival and seed sweeps are bounded evidence, not a proof of unique induction. Owner exact-byte integration, fresh native qualification, acceptance replay, and any training admission remain pending; `training_admitted` is false.
