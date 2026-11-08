# Current notes: 27b865c5f43a

## Intended rule

A lawful input has three isolated monochrome components. Sort them by leftmost
column (top row is the tie-break), binary-crop each component, top-left-pad the
crops to their common dimensions, and place the ordered pairwise ORs in a 3×3
color-8 gallery with one background row/column between panels. The selected
Racket authority is unchanged and pinned by `RULE_HASH = de4d9d03f710`.

## Review-fa7d98e55ec14764 repair

The imported 2.0.1 generator declared eight axes but meaningfully controlled
almost only dimensions. It accepted unknown overrides, mixed intentionally
invalid textures into the ordinary domain, and its validator merely counted
colors. Hard-band defaults also drifted outside canonical profiles. The repair
replaced that contract with five exact, observable axes:

- `grid_h` 8..9 and `grid_w` 17..20;
- four fixed left-to-right palette roles;
- three shape-density sets with observable cell-count signatures;
- four relative row patterns.

Default dimensions cycle only through the four exact canonical profiles. Seeded
reflections and placement jitter retain input diversity without hiding an
advertised control. `self_check` now validates the complete structural grammar,
and metadata cannot waive invalidity. Exact degenerates are retained at
`counterexamples/review-fa7d98e55ec14764/ordering-degenerates.json`.

## Teaching decisions

All canonical pairs accidentally align left-to-right order with both ascending
source-color order and top-row scan order. The generator now declares executable
`color_sort` and `row_sort` rivals. Non-monotone palettes and non-aligned row
patterns are scheduled densely enough that every tested four-demonstration set,
including every hold-one-out rotation of five consecutive examples, refutes both.
The independent oracle and rival reproducer is `workspace/reference_probe.py`.

## Parametric assessment

`workspace/parametric/gallery_gap.py` is a proposed, isolated prototype with
`gallery_gap ∈ {0,1,2}` and canonical default 1. It materializes and executes a
complete Racket program for each setting. This does not alter or approve the
selected rule. The parameter is easy to teach through output dimensions but may
be too superficial to improve reasoning value.

## Known limits and open findings

- Structural validation intentionally restricts components to canonical-size
  3×3-normalizable crops with 4..8 cells and at least one background-cell buffer.
- Generated `shape_set` observability uses ordered cell-count signatures; lawful
  canonical inputs outside those signatures remain accepted but are not claimed
  to encode a public override state.
- Declared-rival and finite lesson checks do not prove uniqueness against every
  possible hypothesis. The two highest-risk canonical-fitting ordering shortcuts
  are covered explicitly.
- No Racket authority change was made.
## Current reviewer considerations

Source SHA-256: `495ba0e0517cf001c44dfcd69c0ca56e98e4bc767fdcfd76e56e726424be377e`.

# Decisions for review-fa7d98e55ec14764

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical program unchanged and pin `RULE_HASH = "de4d9d03f710"`.

**Original rationale.** The imported generator omitted the pin; the reason was not documented. The bundled canonical program already matches every usable canonical pair.

**Alternatives considered.** Alter the rule to sort by color or top row; alter output spacing; or broaden crop normalization. Those would redefine the task rather than repair its data generator.

**Probe and failure mode.** Canonical Racket smoke, authority sync, task-local parity, and the post-repair solve all use the selected program. A stale or modified authority would change the normalized hash or fail parity. No authority file was edited.

## D2 — Replace the advertised eight-axis contract with five honest axes

**Choice.** Keep only `grid_h`, `grid_w`, `palette_kind`, `shape_set`, and `row_pattern`, each with a finite domain and an observable effect.

**Original rationale.** Unknown. The baseline exposed singleton `palette_size`, `position_bias`, `n_distinct_colors`, and `density` controls and mixed aliases/degenerates into `texture`, but most did not influence generated grids.

**Alternatives considered.** Preserve compatibility by accepting and ignoring old names; mark every old field diagnostic; or invent behavior for all eight. Silent compatibility would keep corrupt curriculum requests looking successful, while inventing behavior would add unsupported complexity.

**Probe and failure mode.** The task test enumerates 768 full combinations per band and recovers the requested state from the grid. The shipped override gate covered 11,880 accepted cases with zero findings. Unknown or mistyped fields now fail explicitly.

## D3 — Anchor every default draw to an exact canonical profile

**Choice.** Cycle dimensions through `(8,17)`, `(8,18)`, `(9,18)`, and `(9,20)` in every difficulty band, while retaining band-specific ordering of those profiles.

**Original rationale.** The baseline sampled wider dimensions by difficulty, apparently to manufacture difficulty, but hard draws changed the input/output size relation and left canonical support sparse or absent.

**Alternatives considered.** Use an envelope rather than exact profiles; retain large hard grids; or make all bands identical. Exact scheduled profiles provide reproducible support and avoid equating canvas size with reasoning difficulty, while per-band schedule order still prevents a single universal start.

**Probe and failure mode.** The pinned profile floor measured 20/20 exact hits in every band and accepted all five canonical inputs. The limitation is intentional: this repair does not claim support for larger lawful canvases.

## D4 — Teach left-to-right order by counterexample, not by prose

**Choice.** Declare executable `color_sort` and `row_sort` rivals and schedule non-monotone palettes and non-aligned row patterns densely enough to refute both in every four-demo lesson and every one-query rotation of a five-pair window.

**Original rationale.** The canonical data accidentally correlates source column, color rank, and top row; both shortcuts fit all canonical labels.

**Alternatives considered.** Randomize without a schedule; add more demonstrations; rely on a written description; or keep only one rival. Pure randomization can produce unlucky ambiguous lessons, and description-only data does not force the model to use the intended cue.

**Probe and failure mode.** Focused tests first prove both rivals fit every canonical pair, then prove explicit generated witnesses disagree. The 12-lesson semantic gate and 300-lesson census found no declared-rival ambiguity under any held-out query position. This is finite rival coverage, not universal identifiability.

## D5 — Use bounded shape families plus seed-level geometric variation

**Choice.** Author three shape sets with distinct ordered cell-count signatures and add bbox-preserving reflections plus placement jitter.

**Original rationale.** The baseline shape path was not documented clearly enough to recover intent. The selected rule needs three distinct crops with a common `3×3` panel size, not arbitrary texture labels.

**Alternatives considered.** Fully random connected-polyomino search, fixed templates only, or rotations that swap height and width. Search would complicate exact override observability and rejection behavior; fixed templates would duplicate too often; dimension-swapping rotations could break layout constraints and semantic state recovery.

**Probe and failure mode.** The task tests require at least 40 unique grids in 48 default samples per band while observing every shape set. A remaining restriction is that authored components contain 4–8 cells and fit canonical-scale crops.

## D6 — Make validation structural and metadata-independent

**Choice.** Parse connected components and validate the complete grammar. Metadata never waives an invalid grid.

**Original rationale.** The baseline checker counted colors and could accept malformed, merged, tied-column, or repeated-crop inputs.

**Alternatives considered.** Validate only generated metadata; trust the generator; or duplicate the Racket transformation as validation. Metadata can lie or go stale, and transformation parity alone does not prove that the input belongs to the intended distribution.

**Probe and failure mode.** Retained counterexamples remain rejected even when misleading metadata is supplied. Canonical inputs and all authored override combinations pass.

## D7 — Keep the gallery-gap rule family isolated

**Choice.** Build `gallery_gap ∈ {0,1,2}` as a runnable task-local parametric prototype with default 1, but do not select it for production.

**Original rationale.** `PARAMETRIC-RULES.md` asks for a meaningful bounded parameter chosen once per episode. Separator width is the cleanest parameter that yields complete executable rules without changing object semantics.

**Alternatives considered.** Parameterize source ordering, panel size, output color, or Boolean composition. Ordering and composition would produce materially different concepts with harder legal-input constraints; output color is even more superficial; panel size requires a broader source-shape grammar.

**Probe and failure mode.** Each of the three programs was executed by the bundled Racket runtime; four demos and the query distinguish every alternative. The parameter is visually obvious from output dimensions, so evidence does not show extra training value; status remains `proposed_prototype_not_selected`.

## D8 — Keep audit fixes out of the repair delta

**Choice.** Record source-bound counterexamples for `aaabf5b57a80` and `8387b52c80df` without editing either target.

**Original rationale.** The assignment explicitly separates peer audits from the owned repair and says no audit fix is required.

**Alternatives considered.** Opportunistically repair their override contracts. That would broaden the delta, mix ownership, and make source-bound intake harder.

**Probe and failure mode.** `checks/audit/*/override-contract-witness.json` records exact source/rule hashes and public call recipes. The findings remain open for their owners.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/27b865c5f43a/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
