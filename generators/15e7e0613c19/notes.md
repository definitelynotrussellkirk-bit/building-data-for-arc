# 15e7e0613c19 — current generator decisions

Version 1.2.0. Canonical rule hash: `1f1935df6364`. Generator SHA-256:
`0c8171c8bf81df45cc1ffd8916213712758a96612552e8c9fc5f353873242a17`.

## Intended rule and domain

Extract nonzero monochrome four-connected components. Sort by occupied pixel count,
then bounding-box height, width, and numeric color, all ascending. Crop each
component separately; pack left to right, top aligned, with one zero column
between crops. Separate components of the same color stay separate.

The input domain has a majority-zero background, two to five separated motifs,
integer colors 1–9, and one to five occupied cells per motif. The nonmutating
validator rejects malformed/ragged grids, booleans, floats, invalid colors,
adjacent distinct motifs, and outputs beyond 30 rows or columns. This is a
restricted generator domain, not every grid accepted by the canonical program.

## Exact controls and distribution

`grid_h` is 7–14; `grid_w` is 9–16; `n` is 2–5. `palette_size` and
`n_distinct_colors` are exact aliases, both counting every realized color,
including zero, in 2–6. Aliases must agree and colors cannot exceed `n+1`.
Impossible combinations raise structured errors; unknown/retired controls fail.

Every band uses a 75% canonical-profile mixture over (7,9), (7,10), (8,11),
and a 25% broader dimension draw. All nine foreground colors are available.
Bands salt random layouts; they do not claim calibrated cognitive difficulty.

The default three phases teach pixel-vs-bbox area, height/width tie breaking,
and color ties/repeated-color segmentation. Five demonstrations plus one query
contain two examples of each phase; holding out any one pair preserves a
refuting demonstration for every declared rival. Phase profiles repeat;
concrete palettes/layouts/dimensions do not. No full schedule-period claim is made.
Count overrides outside the phase's default count/color setting use the lawful
general sampler and are outside this curriculum guarantee.

## Reversals and evidence

The inherited vertical-packing/per-color descriptions were incorrect; the
canonical program and all three labeled canonical pairs establish horizontal
packing of connected components. The previously ignored style/color axes were
replaced by the five observable controls, rather than preserved as promises.

The first repair used wide horizontal teaching motifs. The full after battery
found 22/60 outputs with a reshape relation absent from canonical examples.
The final phases use a vertical five-cell line, a vertical four-cell line, and
vertical dimers respectively, preserving all witnesses while shrinking both
output dimensions. `checks/repair-default-shrink/` retains the failing source
and regression; `checks/final-battery/` records all 12 checks passing.

`counterexamples/bbox-area.json` is an exact generated, Racket-verified witness.
`workspace/probe_shortcuts.py` regenerates all five rival witnesses and verifies
public Racket receipts. The task-local tests include the authoritative fixture,
canonical support, exact-control corners, invalid inputs, and lesson rotations.
See REVIEW.md and RESULTS.json in the return for final counts and fresh replay.

## Limits and proposed extension

Finite motifs and a three-phase curriculum may admit undeclared shortcuts.
The finite-rival checks do not prove universal identifiability. Numeric colors
are a canonical tie breaker, so arbitrary color permutations are not generally
equivariant. The all-color-equal override remains lawful only when components
stay separated. No canonical/Racket authority or training approval changed.

`workspace/parametric/` is a runnable prototype for episode-level `area_order`
ascending/descending. Only the primary comparator changes; ties retain their
canonical ascending order. Its wider controlled fixture domain is separate from
the production sampler. This proposal does not approve the new rule family.
## Current reviewer considerations

Source SHA-256: `0c8171c8bf81df45cc1ffd8916213712758a96612552e8c9fc5f353873242a17`.

# Decisions — 15e7e0613c19

## Authority and original evidence

The original source was version 1.1.1, SHA-256
`e6c5134f4d278132a035a6480492c7ed08c93fbb8efcadce2884f3fb9316addd`.
Its notes were a placeholder; no retained review index or selected task tests
were present. No prior return was treated as a measurement of this source.
The canonical row supplied three labeled pairs. Racket, the canonical ledger,
selected base solution, catalog, and shared helpers were not edited.

The actual rule extracts monochrome four-connected nonzero components, orders
by `(pixel count, bbox height, bbox width, numeric color)`, and horizontally
packs the individual crops, top aligned with one zero column between crops.
The generator's vertical-packing and per-color-merge descriptions were reversed
because they disagreed with the authority. The rule hash is now pinned.

## Input decisions and alternatives

| Choice | Original problem or unknown rationale | Decision and evidence | Limit or rejected alternative |
| --- | --- | --- | --- |
| Components | Motifs excluded singleton/dimer support present in canonical examples. Original rationale unknown. | Include one-to-five-cell connected motifs and separated repeated colors; all three canonical inputs accepted. | This does not cover every component shape the Racket rule can process. |
| Dimensions | Declared 7–14 by 9–16 controls were rejected using band-specific defaults; canonical profile hits were 0/60. | Exact controls honor the full declared ranges. A 75% canonical-profile mixture plus 25% broader draw operates in every band. Final exact/envelope hits 44/60: easy 14, medium 14, hard 16. | Always forcing canonical dimensions would remove useful broader support. Random broad-only dimensions failed the observed profile floor. |
| Object count | Counts were not coupled cleanly to palette requirements. | Exact `n` in 2–5. General placement has a bounded randomized path plus a nonclipping deterministic shelf fallback. | Impossible color/object combinations are rejected explicitly, never clamped. |
| Color count | `palette_size`, `n_distinct_colors`, palette/style metadata were ignored or unobservable. | Both count controls include zero, range 2–6, and must agree. All foreground colors 1–9 are sampled. | Retired style/texture/density/position axes are rejected, a deliberate compatibility change. Do not pass old unused controls expecting them to be ignored. |
| Separation | Original checking did not establish a strict valid domain for all accepted values. | Majority zero, a background moat between distinct motifs, rectangular integer grids, and packed-output bounds are checked without mutation. | Neighboring differently colored components may be legal for Racket but are outside this generator's deliberately separated domain. |
| Teaching support | Canonical examples allow bbox-area sorting, omitted tie breakers, and per-color merging. | Five executable rivals, five witnesses, bindings, and a lesson ambiguity hook. Three phases cover all five differences. | A canonical-fitting rival is not evidence that canonical labels are wrong. |
| Output shape | The first repair produced 22/60 reshape outputs; canonical examples only shrink. | Rotate the five- and four-cell lines vertically and use vertical dimers in the repeated-color phase. Default output height is at most 5 and width at most 8, below the minimum 7×9 input. | Keep the failed first repair and regression, rather than suppressing the drift detector. Arbitrary count overrides remain reference-lawful but do not promise the default shrinking curriculum. |
| Difficulty | No evidence justified a cognitive difficulty ranking. | Keep easy/medium/hard as reproducible random salts with canonical support in all three. | Do not claim calibrated difficulty or force unrelated complexity changes to satisfy labels. |

## Demonstration and query policy

`EXAMPLES_NEEDED = 5`. The production census uses five ordered demonstrations and
one query from six accepted consecutive generated pairs. Semantic phases cycle
0, 1, 2; six pairs contain two of each. Holding out any one still leaves each
phase among the demonstrations. Query rotations preserve the order of the other
five pairs. The generator declares profiles, not `LESSON_SCHEDULE_PERIOD`:
concrete grids do not repeat every three samples, so a full-period declaration
would be misleading.

The strict semantic smoke test passed 12/12 production lessons and all 72 query
rotations. The larger census is retained as three complete band shards, each
requesting 100 lessons with the same official seed/start recipe and required
rotation policy. Counts and complete receipts are in REVIEW.md and RESULTS.json.
The two earlier combined runs hit storage exhaustion and remain explicitly
incomplete; their partial results are not substituted for complete shard passes.

The guarantee applies to defaults and dimension overrides that preserve the
phase's object/color counts. Other lawful exact-count overrides use a general
sampler, and their teaching support is not certified. Arbitrary nonconsecutive
example selection and fewer than five demonstrations are also not certified.
The official final solve uses five demonstrations and two masked queries; its
preparation receipt separately confirms declared competitors were refuted.

## Shortcut assessment and new restrictions

All five declared rivals fit all three canonical labeled pairs. Pixel-count
sorting versus bbox-area sorting is the clearest single rival because sparse
shapes invert those two orders. The final generator emits an exact separating
case at seed 0, sample 0, medium; `QUESTION_ANSWER.md` prints it and cites the
public Racket receipt. Height, width, color and repeated-color witnesses are
also found in the first three draws and Racket verified.

Self-review: default shape families and the semantic phase cycle remain finite,
so a learner could exploit a shape lookup or an undeclared phase shortcut.
Broader layouts, dimensions, all nine foreground colors, reflections, and exact
count overrides expand support, but the reported finite-rival passes do not
prove absence of all such shortcuts. Some phase-specific palette ordering is
constrained to expose tie-break witnesses, so random palettes alone do not
establish independence from color rank. Colors participate numerically in tie
breaking, so arbitrary color permutations are not valid equivariance tests.

## Parametric-rule assessment — prototype

A suitable small parameter is episode-level `area_order` in
`{ascending, descending}`. It is drawn once per episode. Descending reverses
only the primary occupied-pixel comparator; equal-area height, width and color
ties retain canonical ascending order. Horizontal packing, top alignment and
gap one remain fixed. Reversing the entire comparator would incorrectly reverse
tie semantics and was rejected.

`workspace/parametric/prototype.py` instantiates and executes the actual Racket
program. The default is exactly the canonical `program_solution` text. Its full
program SHA-256 is `1f1935df636413d3fc6d97308330be436dbd5a21e3e688736e8c5f2ed546d224`;
the descending program is `ebdd1e11e70bfbac39e4d26450d8941c586bef400cf46965dbfd13a052796b22`.
These hash full wrapped programs; the public apply tool separately hashes the
executed canonical body as `824fd14598bea95eea23d02f6d84510a5ac6a49ac877ca03bc9c59a68a543ddb`.

Two distinct settings were exercised: seed 1 ascending and seed 0 descending,
each with three demonstrations and one query. Eight labels, eight rival outputs
and two shared-witness outputs were executed in Racket. Demonstrations 0 and 2
distinguish the settings in both episodes; the equal-area demonstration verifies
unchanged tie behavior. Four prototype tests passed, including all three
canonical labels for the default. Exact commands and instantiated programs are
under `checks/parametric/`.

The fixture sampler uses wider controlled inputs and some motifs larger than
the production domain. It is a proposed rule-family prototype, not a production
sampler replacement or training admission. The canonical rule was not changed.

## Evidence and environmental decisions

Blind solving finished before any generator or canonical rule was opened.
The later exposed solve declares earlier exposure yes and reference consultation
no during solving. Each had one actual implementation/check attempt; none was
invented. Their masked-query correctness is unknown. Notes are agent-authored
work logs, not captured token-level model traces.

The original archive has 76,129 files and needs about 1.08 GB expanded, beyond
the available workspace at extraction. The optional recovery tooling streams
and verifies all original members, materializes a dependency closure, saves
random seeds before deriving assignments, and retains immutable hash-linked
receipts. It never rerolls an assignment. Two original full extraction failures,
two incomplete census runs, two storage-blocked task-test attempts, and the real
first-repair failure are retained.

The sparse return uses an explicit archive-backed packager. Unmaterialized
original source bytes are checked from the verified original archive, while
materialized paths and edits are checked physically. The original scope rules,
patch assembly and official return validator remain in force. A full physical
source-tree check was not run. The maintainer must decide whether to accept this
clearly reported verification scope; the optional shared tooling and parametric
prototype remain separate proposals. Fresh replay uses the official declared
runtime-dependency closure and its own environment; exact final results are in
REVIEW.md and RESULTS.json.

## Final handoff verification

The official replay extracted 331 original files, verified the fresh Git root,
and applied all eight changed paths. Their post-application and post-test hashes
match the reviewed tree. The final source patch SHA-256 is
`c2b1b5ba899f8be4145b84750f410d4a56a88d19df09653ac9e611e4eee57e73`.
A newly created Python environment and newly installed pinned Racket ran the
complete task-local suite: 12 tests and 38 subtests passed. The replay did not
share changed task sources with the authoring tree. Dependency-closure scope
is explicit; this was not a full 76,129-file extraction. See
`checks/fresh-verification.json` and the original replay receipt.

The prototype test was initially placed under repo/tests and was moved to the
required task-local tests directory before final validation; both historical
and corrected commands are retained. A later metadata-only environment probe
omitted a required root-discovery argument; its actual failure is retained and
the corrected probe verifies the fresh source/runtime identities. Neither was
a generator or Racket failure.
