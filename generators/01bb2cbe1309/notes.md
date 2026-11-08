# Current native extension: 01bb2cbe1309

The native extension is complete as a separate proposed family. Production
`v2.0.0` remains unchanged: `generator.py` SHA-256
`f41ab65c06dc6d8627f1a44e5ac6967a6b2ad363f3afe7a45924a573118f0b7a`.
The rule pin remains `d45fd86e0516`; the exact canonical source SHA-256 is
`d45fd86e0516e180c816a4d515424f4a463a9fa1cc3565fcb0fd527ae74786db`.
The historical production notes below are preserved.

## Native rule and request contract

`passes=1` returns the exact canonical program. `passes=2` executes that same
body twice, binding the first completed grid as the second pass's input.
Each pass reads its own original grid, visits 2×2 windows in row-major order,
and accumulates writes separately; later eligible windows win conflicting
writes. The second pass can enable further fills and conflicts. This is an
exact one/two-pass rule, rather than iteration to stability.

The native grammar accepts every rectangular list-of-lists ARC grid with both
axes in 1..30 and exact integer colors 0..9, including blank, thin, overlapping,
and conflicting inputs. Strict controls allow 2–6 demonstrations and 1–4
queries. The ordinary default is **three demonstrations and four queries**;
qualification explicitly requests **six demonstrations and four queries**.
A fixed six-demo/four-query bank is matched across settings, with independent
setting/demo/query random streams and stable prefixes when counts change.
Its ten distinct inputs include dense 30×30 demonstration and query profiles
with different geometry.

## Current retained evidence

Paths below are relative to `WORK`.

| Check | Current result |
| --- | --- |
| Combined focused suite | **157 passed** |
| Sampler | **96/96 requests passed**, `checks/01bb2cbe1309/sampler-v3.json` |
| Native manifest | **13 bound files** |
| Native qualification | **4 qualified jobs; 64 protected evaluations**, `checks/01bb2cbe1309/qualification/qualification.json` |
| Independent teaching audit | **80 hypothesis/episode fits: 72 refuted, 4 intended survivors, 4 equivalent one-pass aliases; no surviving query disagreements** |
| Protected teaching execution | **172 evaluations; all 40 intended labels checked**, `checks/01bb2cbe1309/diagonal-teaching-audit-v2/private/audit.json` |
| Causal witness and replay | **2 cases; `reviewer_replayed`**, `checks/01bb2cbe1309/causal/replay.json` |
| Sequential public preview | **16 views exported and verified**, `checks/01bb2cbe1309/preview/` and `checks/01bb2cbe1309/preview-verify-command.json` |

The teaching audit covers both settings at seeds 0 and 17. Survivors are fixed
from the first two demonstrations before query checks. The four extra
survivors are the one-pass `skip_A` and `reverse_second_snapshot` aliases,
which are equivalent because no consuming second pass exists in that setting.

## Corrections and limits

The construction received a density repair for the large profiles. The
ordinary CLI demonstration default was corrected to three while qualification
remained explicitly at six. An audit-only Racket primitive was corrected from
`grid-set` to `set-cell`; this did not change the canonical authority or
production generator. Prior sampler, audit, failure, and command receipts
remain retained; the current receipts above identify the completed build.

These are finite checks of the declared hypotheses, settings, seeds, labels,
and requests. They establish neither universal unique induction nor uniform
sampling of the full native grammar. The two causal replays validate protected
output labels; intermediate metadata and causal interpretation are authored
claims, and no training gain is measured. Public preview verification checks
the serialized projection without a new Racket replay. Owner qualification
and fresh acceptance remain pending; **no training data are admitted**.

---

# Working notes: 01bb2cbe1309

## Review repair

- Preserved the canonical Racket authority (`RULE_HASH = d45fd86e0516`).
- Replaced rule-hiding/dead textures and uncontrolled blocked counts with four explicit scene profiles: `canonical`, `blocked`, `axis`, and `mismatch`.
- Set `EXAMPLES_NEEDED = 4`; every four consecutive samples contain all profiles.
- Exposed only exact observable controls: `grid_h`, `grid_w`, and `scene_profile`.
- Added strict component-grammar validation, an independent Python rule mirror, semantic witnesses/rivals, canonical shortcuts, and lesson-level identifiability.
- Added focused task tests and `workspace/lesson_probe.py` for 100-lesson-per-band production/cyclic censuses.

## Measured final source

Generator SHA-256: `f41ab65c06dc6d8627f1a44e5ac6967a6b2ad363f3afe7a45924a573118f0b7a`.

All task-local tests and all twelve repository stages passed independently. The exact combined battery command stalled after its third completed stage; see the review return's `FEEDBACK_TO_CODEX.md` and retained timeout evidence. The source-bound lesson census found no harmful survivors among the declared rivals on seeds 0–99 in any band or cyclic start. These are finite results, not universal induction guarantees.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `f41ab65c06dc6d8627f1a44e5ac6967a6b2ad363f3afe7a45924a573118f0b7a`.

# Design decisions: 01bb2cbe1309

The baseline had almost no retained design notes, so I distinguish source-stated intent from inferred rationale. Finding IDs match `REVIEW.md`.

## D1 — Preserve the canonical Racket authority

**Choice.** Keep the selected rule unchanged and pin `RULE_HASH = "d45fd86e0516"` in the generator.

**Original rationale.** The baseline Python summary already described the canonical behavior, and its live rule smoke passed before repair. There was no evidence that the authority was wrong.

**Alternatives considered.** Rewrite or simplify the Racket source; switch to the divergent archival source.

**Why rejected.** The assignment was a generator-distribution repair. Altering a canonical rule that already solves all train/test pairs would add risk without correcting the observed defects. Final authority sync confirms the selected canonical and task-rule sources remain synchronized and execution-correct.

**Failure mode / limitation.** An archival raw source remains textually different while execution-equivalent. I did not normalize it because it is outside the selected authority and unnecessary for this repair.

## D2 — Remove rule-hiding textures instead of trying to rehabilitate them (R1)

**Choice.** Remove `plain`, `no_dominoes`, `full_2x2`, and `single_cell` texture controls. The final generator always produces at least one lawful positive motif and uses named semantic scenes for negative evidence.

**Original rationale.** The baseline docstring called the three degenerates “rule-hiding inputs.” The intended training use of such samples was otherwise unknown. `plain` was declared helpful but was behaviorally dead.

**Alternatives considered.** Keep the textures but mark them incompatible with normal training; keep only `plain`; turn degenerate samples into an auxiliary split.

**Why rejected.** The strict task contract requires learnable examples. Blank, singleton, and already-filled boards hide the rule, overlap the declared domain, or fail `self_check`; they consume training capacity without teaching a transformation. Named semantic negatives are more informative because each isolates one necessary condition while retaining a positive example.

**Failure mode / limitation.** The generator no longer covers “nothing happens anywhere” boards. That is deliberate; query identity behavior is still demonstrated locally by the negative component inside a board that also contains a positive transformation.

## D3 — Use a deterministic four-scene curriculum (R2)

**Choice.** Schedule `canonical → blocked → axis → mismatch` by `sample_index mod 4` and set `EXAMPLES_NEEDED = 4`.

**Original rationale.** Baseline comments intended three demonstrations to show both diagonal orientations and at least one blocked pair, but the sampler drew `n_blocked` independently from 0–2 and did not guarantee that intention. Axis-aligned and unequal-color counterexamples were mentioned only in comments, not generated.

**Alternatives considered.** Keep three demos and pack multiple negative types into one board; sample profiles randomly with minimum expected rates; add only a blocked profile.

**Why selected.** Four single-purpose scenes make each condition independently legible and guarantee coverage in every consecutive lesson. A four-state cycle is cheap to audit exhaustively over every start offset. Packing several negatives into one example would reduce attribution clarity; random rates would permit unlucky shortcut-surviving lessons.

**Failure mode / limitation.** The deterministic order is learnable metadata if a consumer exposes sample order across many lessons. The shapes, colors, anchors, orientations, and motif counts remain randomized, and the semantic profile is not itself part of the model-facing grid metadata. Future exporters that randomize demo order retain the same evidence set.

## D4 — Treat both diagonal orientations as positive evidence, not separate negative profiles

**Choice.** Alternate positive motif orientation inside each board. Canonical-size boards contain exactly two positive motifs, one main and one anti diagonal. The canonical scene therefore refutes both orientation-only rivals.

**Alternatives considered.** Add `main_only` and `anti_only` schedule profiles; require every scene to contain both orientations.

**Why selected.** The former would expand the minimum lesson without adding a new semantic condition. The latter becomes awkward at the smallest exact override after reserving one anchor for a negative. A guaranteed canonical scene is sufficient and is verified by the witness/rival contract.

**Failure mode / limitation.** A single negative-profile board at the smallest dimensions may contain only one positive orientation. Identifiability is a lesson-level property, not a requirement that every individual grid refute every rival.

## D5 — Replace the broken `n_dominoes` contract with only observable exact axes (R2)

**Choice.** Expose `grid_h`, `grid_w`, and `scene_profile`. Validate unknown names and types before generation. Provide `observe_overrides` so the repository gate can recover the realized values.

**Original rationale.** The baseline advertised `n_dominoes`, but generated with an internal draw named `domino_count`; the documented override was therefore not consumed. The reason for the mismatch is unknown.

**Alternatives considered.** Repair `n_dominoes` and retain `n_blocked`; expose colors, orientation, or motif count as additional controls.

**Why selected.** The three retained controls are sufficient for data slicing and all combinations are feasible. Motif count is intentionally coupled to shape and difficulty to avoid overcrowded boards; exposing it would require a substantial incompatibility matrix. Color and orientation are nuisance variation rather than useful dataset axes.

**Failure mode / limitation.** Consumers cannot request an exact motif count. If that becomes necessary, it should be added with an explicit capacity function and structured incompatibility declarations, not an approximate override.

## D6 — Separate semantic profile from shape profile

**Choice.** Draw the semantic profile from the four-cycle and shape from an independent canonical-weighted schedule. Three fifths of default samples use exact canonical shapes; the rest use difficulty-specific broad shapes.

**Original rationale.** The baseline varied dimensions by difficulty, presumably for coverage, but did not guarantee canonical-profile support.

**Alternatives considered.** Use only canonical shapes; use only broad difficulty shapes; assign one shape to each semantic profile.

**Why selected.** Canonical weighting satisfies profile-floor and distribution alignment while broad shapes prevent trivial memorization. Independence avoids a shortcut such as “blocked examples are always 5×6.” The measured profile floor was 38 exact hits in 60 draws, with support in every band.

**Failure mode / limitation.** Strict canonical-like rate is deliberately 14.2%, not a majority. This is enough to bind the generator to the canonical envelope while preserving broader training variation.

## D7 — Use exactly two colors and separated 2×2-local components

**Choice.** Sample two distinct colors from 1–9, paint 2–8 local components, and separate anchors by at least one empty row or column.

**Original rationale.** The baseline used distinct colors and attempted 2×2 anchor separation. Exact palette intent was not documented.

**Alternatives considered.** One color; arbitrary 1–9 color palettes; dense overlapping motifs.

**Why selected.** Two colors are enough to demonstrate color copying and unequal endpoints while keeping the local rule readable. Separation prevents accidental cross-component 2×2 windows and makes `self_check` able to classify the generated grammar exactly. Dense overlaps would test scan-order interactions not present in the canonical examples and would make rival attribution harder.

**Failure mode / limitation.** The generator intentionally excludes overlapping target windows and palette sizes above two. It therefore teaches the canonical local rule in a clean domain rather than claiming universal coverage of all grids accepted by the Racket function.

## D8 — Make `self_check` a grammar validator, not merely a positive-witness counter

**Choice.** Validate ARC shape/cell types, 8-connected component locality, supported motif kinds, positive presence, at most one negative, and exactly two nonzero colors.

**Original rationale.** The baseline check only counted clean diagonal pairs, so malformed or unintended structures could pass as long as one target existed.

**Alternatives considered.** Keep a permissive validator and rely on generator construction; validate by comparing output only.

**Why selected.** A strict source-domain validator catches future drift and makes override observation reliable. Output-only checks would miss distribution defects and ambiguous nuisance structures.

**Failure mode / limitation.** Color swaps are intentionally accepted because colors are symbolic; the repository mutation-sensitivity report therefore rejects 56/71 destructive mutations, with all 15 color swaps accepted. That is correct behavior, not a missed error.

## D9 — Declare rivals and test whole lessons (R3)

**Choice.** Add executable `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable`. Build `workspace/lesson_probe.py` to inspect the production sampler and all cyclic starts.

**Original rationale.** Baseline comments named several rivals but supplied no executable contract or retained lesson census.

**Alternatives considered.** Test witness frequency only; hard-code rivals in an external probe; rely on the repository's 12-lesson semantic smoke sample.

**Why selected.** A witness can be frequent while complete lessons still omit it. The probe imports declarations from the generator, verifies that claimed shortcuts really fit every canonical pair, and scores survival after the full demo set. One hundred lessons per band materially exceeds the smoke sample while remaining cheap.

**Failure mode / limitation.** Declared rivals are not exhaustive. The `ffdc7818d842` audit demonstrates why future tooling should also synthesize structural aliases rather than trusting only author-declared rivals.

## D10 — Keep the all-in-one battery timeout visible (R4)

**Choice.** Preserve the failed exact battery command, then rerun every stage independently from the same final source hash.

**Alternatives considered.** Report the independent passes as though the exact command succeeded; omit the wrapper failure; continue waiting indefinitely.

**Why selected.** The exact command is a required workflow and its orchestration defect is actionable. Independent stage receipts establish task-source correctness without erasing the infrastructure failure.

**Failure mode / limitation.** This return cannot prove why the parent process stalled. The evidence only localizes it: the first three stages completed, the fourth emitted no terminal line in the combined run, and the same fourth stage completed in 10 seconds independently.
