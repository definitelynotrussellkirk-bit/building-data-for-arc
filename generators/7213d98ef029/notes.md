# Working notes: 7213d98ef029

## Review diagnosis

The imported `2.0.1` generator produced lawful header matrices, but most of its
advertised controls were not connected to pixels. It also exposed deliberately
invalid textures as ordinary exact overrides, omitted `RULE_HASH`, silently
accepted unknown override names, had no executable semantic contract, and
sampled dimensions/palettes that only weakly overlapped the canonical ledger.
The immutable baseline rerun is retained under
`checks/before-retrospective/` in the review return.

## Selected design

Version `3.0.0` keeps only three exact, pixel-observable controls:

- `shape_profile`: the four distinct canonical output dimensions;
- `scene_profile`: `all_shared`, `row_gap`, `col_gap`, or `dual_gap`;
- `palette_kind`: four four-color palettes plus one five-color `wide` palette.

The default schedule is deterministic. Any four consecutive samples contain all
four scene profiles, at least two shapes, and at least two palettes. Header
construction always supplies matches and mismatches, an off-diagonal match, a
diagonal mismatch, and a repeated shared color. Partial overrides are completed
constructively. Nine exact triples involving `wide` are impossible because the
short axis cannot hold the required palette roles plus a repeated shared color;
these triples are declared in `INCOMPATIBLE_OVERRIDE_COMBINATIONS` rather than
rejected silently.

## Semantic contract

`strict_canonical_like` defines the ordinary manifold. Five witnesses and five
paired rivals test the central distinctions: row-only and column-only colors
must produce zero strips, repeated shared colors create full cross-products,
and equality is not restricted to the diagonal. `lesson_identifiable` requires
a four-demo lesson to cover all scene profiles, vary shape and palette, agree
with the selected rule, and refute every declared rival.

`workspace/lesson_probe.py` is a source-bound larger census. The retained run
sampled 100 sliding four-demo lessons per band (400 demos per band), found all
300 lessons identifiable, all 1,200 inputs unique within band, and refuted every
declared rival in every lesson. It is a finite census, not a proof that every
possible learner will infer the rule.

## Limits and rejected alternatives

- Arbitrary dimensions were rejected in favor of the canonical four-shape
  support. This improves ledger overlap but intentionally narrows morphology.
- Free numeric `n_shared`, `palette_size`, and `n_distinct_colors` controls were
  rejected because they create a large compatibility surface and are not needed
  to teach the rule. Their meaningful effects are represented by the scene and
  palette axes instead.
- Invalid `no_shared`, `all_same_color`, and `corner_marked` textures were
  removed from the ordinary domain. Malformed examples belong in validator
  tests, not training draws.
- A rejection-sampling constructor was rejected. The final constructor is
  finite, deterministic, and checks that requested axes are recoverable from
  pixels.
- The fixed palette bank is intentionally small and should not be interpreted
  as universal color coverage. Across scheduled draws it uses all ARC colors,
  while individual examples use canonical-like cardinalities.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `46ef37fa96e213a9e51f1ae0e7891cdc9c4571cbc90f6a4dbe6bfe76970998d2`.

# Design and review decisions — 7213d98ef029

## D1 — Preserve the selected Racket authority

**Input evidence.** Canonical examples and the baseline rule smoke showed that
the transformation itself was correct: remove the top/left header axes and
write the row color at every row/column equality. The baseline authority sync
and Racket lint were green. The original rationale for the exact Racket source
was not documented beyond imported metadata.

**Decision.** Do not edit the Racket rule. Pin `RULE_HASH = "e5bbb5dc0c42"` and
build an independent Python `rule_mirror` for parity and semantic probes.

**Alternatives rejected.** Rewriting the rule merely to accompany a generator
repair would add authority risk without fixing the data defects. Final evidence:
120/120 mirror parity and synchronized authority in `checks/after/`.

## D2 — Replace the dead control surface instead of emulating it

**Input evidence.** The baseline advertised nine controls, but ordinary draws
used essentially only dimensions. Helpful textures were byte-identical,
invalid textures occupied the ordinary valid domain, provenance draws for
several numeric axes were missing, and unknown names were silently swallowed.
See R1 in `REVIEW.md` and the baseline lint/override logs.

**Decision.** Reduce the public API to three exact controls whose values can be
recovered from pixels: shape, header-set relationship, and palette.

**Alternatives rejected.** Wiring every legacy numeric control independently
would create a large compatibility matrix with many semantically redundant or
impossible combinations. Keeping diagnostic-only axes would preserve misleading
metadata. The effects that matter for learning—dimensions, shared/unshared
roles, and palette cardinality—are represented directly.

## D3 — Use exactly the four canonical output shapes

**Input evidence.** The five canonical pairs use four distinct output shapes:
`4x5`, `5x4`, `4x6`, and `5x5`. The baseline sampled additional dimensions and
had weak exact-profile overlap, including zero hard-band support in the 20-draw
baseline check.

**Decision.** Define `SHAPE_PROFILES` as those four dimensions and schedule all
of them across seed/sample/band combinations.

**Alternative rejected.** A broad arbitrary-dimension range offers morphology
variety but spends training mass outside the ledger. This repair prioritizes
canonical support; the restriction is explicitly documented as a limitation.
Final profile evidence is 39/60 exact and 60/60 envelope.

## D4 — Make header-set relationships the semantic scene axis

**Input evidence.** Equality-matrix understanding requires more than one shared
color. A learner must see that a color present on only one axis produces a zero
row/column, while repeated shared colors produce a full Cartesian product.

**Decision.** Use four scenes: `all_shared`, `row_gap`, `col_gap`, and
`dual_gap`. Every scene still contains both equality and inequality cells, and
construction forces off-diagonal equality plus diagonal inequality.

**Alternatives rejected.** A raw `n_shared` integer does not state which axis
owns unmatched colors and does not by itself guarantee an identifiable lesson.
The old `no_shared` negative was rejected because it produces no positive
signal and is outside the ordinary strict manifold.

## D5 — Cover both canonical palette cardinalities with fixed palettes

**Input evidence.** The canonical ledger includes total palette sizes five and
six (background plus four or five nonzero header colors). An intermediate
four-color-only repair failed the distribution gate with
`canonical_palette_unreachable`; the failure is retained in `checks/dist/`.

**Decision.** Keep four fixed four-color palettes and add `wide`, a five-color
palette. Fixed named sets make palette overrides exactly observable and avoid
color-count ambiguity.

**Compatibility decision.** Five nonzero roles plus the repeated-shared-color
teaching invariant do not fit every short-axis scene. Exactly nine impossible
shape/scene/`wide` triples are declared. Every one- or two-axis partial request
still has a constructive completion.

**Alternatives rejected.** Dropping the repeated-shared witness would make
`wide` universally fit but weaken lessons. Random palette sets would make a
named exact override hard to observe and reproduce. Rejecting every partial
`wide` request would be unnecessarily restrictive.

## D6 — Require four demonstrations and use a sliding scene schedule

**Input evidence.** Three examples cannot each uniquely cover all four set
relationships. Individual witness frequency also does not prove that a complete
lesson contains all distinctions.

**Decision.** Set `EXAMPLES_NEEDED = 4`; `sample_index mod 4` schedules one of
each scene. Shapes and palettes rotate independently. Every cyclic four-sample
window therefore includes all scenes, while `lesson_identifiable` also requires
at least two shapes and two palettes.

**Alternatives rejected.** Independent random scenes risk incomplete lessons.
A fixed non-sliding block could pass only when lessons happen to start at index
0. The larger probe uses starts `0..99`, repeatedly testing all cyclic offsets.

## D7 — Construct compatible examples directly

**Input evidence.** The baseline used an unbounded `while True` to wait for a
shared color. Complex override interactions would make rejection sampling less
predictable and harder to audit.

**Decision.** Enumerate compatible `(shape, scene, palette)` tuples, choose a
deterministic scheduled completion around pinned axes, assign explicit color
roles, fill remaining header cells from lawful role sets, and choose a column
permutation that exposes the required witnesses. Assert both strict validity
and pixel-observed axis equality before returning a fresh grid.

**Alternatives rejected.** Rejection sampling, silent fallback, and clipping a
requested control all obscure whether an exact override was honored.

## D8 — Harden validation and invalid-call behavior

**Input evidence.** The old `self_check` assumed rectangular integer grids and
could crash or misdiagnose malformed inputs. Invalid textures were generated as
ordinary inputs, and unknown overrides were accepted.

**Decision.** Add structural checks for empty/ragged grids, ARC color type/range,
size, corner/header/interior grammar, and positive/negative rule signal. Reject
unknown difficulties, axes, and values with `ValueError`; return precise error
lists for malformed grids.

**Alternative rejected.** Retaining malformed textures as “degenerate
examples” would mix validator tests into training data. They now appear only in
regression tests.

## D9 — Declare executable witnesses and rivals

**Input evidence.** The baseline semantic gate reported `NO_CONTRACT`. A clean
rule parity result does not show that demonstrations disambiguate the intended
rule.

**Decision.** Pair five witnesses with five plausible wrong rules:
row/column-only headers incorrectly forced to match, first matching column only,
first row per color only, and diagonal-only equality. `lesson_identifiable`
validates outputs, coverage, nuisance variation, and per-lesson rival
refutation.

**Limits.** These rivals are plausible, not exhaustive. The contract demonstrates
specific teaching support and does not prove universal human or model induction.

## D10 — Add a source-bound large lesson probe

**Input evidence.** The shared semantic battery checks only 12 lessons, while
the assignment asks for at least 100 lessons per band when canonical shortcuts
are plausible.

**Decision.** Build `workspace/lesson_probe.py`. It loads the exact generator
bytes, records their hash, iterates `LESSON_COMPETITORS` from the module rather
than copying rival names, samples 100 sliding lessons per band, and reports the
sampler, domain limits, unique inputs, observed axes, demo disagreements, and
lesson-level refutations.

**Result.** 300/300 lessons identifiable; 1,200/1,200 inputs unique within band;
all rivals refuted in all 100 lessons per band. This tool is reusable by future
reviewers and is covered by a task-local regression test.

## D11 — Preserve failures and separate audit-only findings

The immutable baseline rerun is labeled retrospective because the first
monolithic invocation was interrupted. The intermediate four-color distribution
failure is retained rather than overwritten. The two assigned audit targets
were not edited: `07ab476607b3` received a clean finite audit, while
`generic_slot_match_gen1` received a source-bound ambiguity reproducer and an
exact Racket replay. Those results are reported separately in `AUDIT.md` and do
not affect the repaired task's source hash.

## D12 — Final handoff policy

The source used for all final checks is SHA-256
`46ef37fa96e213a9e51f1ae0e7891cdc9c4571cbc90f6a4dbe6bfe76970998d2`.
The exact generated delta was applied with `git apply --check` to a fresh
extraction of the original uploaded ZIP. The patched generator hash matched the
final source, and the selected tests passed 8/8 in that fresh copy. Evidence is
under `checks/final-handoff/` and the exact commands are recorded in
`RESULTS.json`. No source changed after that replay.
