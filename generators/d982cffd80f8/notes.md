# Current design: d982cffd80f8 v3.0.0

## Rule and valid inputs

Use the unchanged canonical Racket authority, pinned by `RULE_HASH =
"58201e67a052"`. Fill an original zero cell iff all eight original neighbors
share one nonzero color. Preserve other cells; evaluate simultaneously.
The positive generator family has one to six fillable centers in a rectangular
integer grid. Touching rings, inert singleton colors, incomplete borders, and
already nonzero centers are lawful. The validator checks that local family,
not whether every colored cell belongs to an isolated hollow ring.

## Reversed decisions and evidence

The imported v2.1.0 validator required exactly two centers for medium samples,
although its generator sampled two or three. Seed 0/index 0 is a compact
counterexample; 199 of 400 medium draws (seeds and indices 0..19) failed the
difficulty-qualified check. Difficulty now controls preferences only, and an
explicit ring count is exact. `counterexamples/medium-validator.json` retains
the original input, validation failure, source binding, and real Racket result.

The old isolated-border requirement also rejected a canonical test input with
an inert singleton. The new local predicate accepts all three labeled canonical
inputs, including touching borders and the singleton. The canonical source and
frozen legacy fixtures remain unchanged.

The old palette controls and constant position/density controls could be silently
ignored. Exact height 5..14, width 5..16, ring count 1..6, and foreground color
count 1..6 are now observed and honored, or fail with structured caller-axis
incompatibility. `n_distinct_colors` remains an exact compatibility alias for
`palette_size`, declared in `OVERRIDE_ALIASES` instead of as an independent
Cartesian axis. Helpful `texture` values alias `palette_kind`; conflicting
aliases and unknown controls fail. The ignored constant controls were removed.
Integer controls and grid colors reject booleans, floats and numeric strings.

## Distribution and teaching

Placement uses shuffled disjoint 3-by-3 tiles with randomized offsets; borders
may touch. Unpinned dimensions prefer familiar sizes and reserve two extra
tiles for a near-ring and a different nonzero center. These controls distinguish
four-cardinal-neighbor filling, seven-of-eight filling, and overwriting existing
centers. Positive centers refute identity. Normal examples include both contrasts;
palette allocation and inert singleton colors realize the exact color count.

Every fifth `(seed + sample_index)` profile prefers a 9-by-9 canvas and three
foreground colors when unpinned. Other draws vary size, count, layout and palette.
This supports canonical profiles without making all examples canonical-sized.
Color families are sampling preferences, not semantic color roles.

`EXAMPLES_NEEDED = 3`. The finite rival registry is executable; its three named
canonical shortcuts fit all canonical pairs. Production lessons use three demos
and one query; query rotations hold out each of the four pairs once while
preserving the other order. Final evidence in return review-9ba11e49eb4dedef
records 300/300 materialized lessons, 1,200 unique inputs and 1,200 rotations,
with zero ambiguities against the four declared rivals. No universal
identifiability or model-training benefit is inferred from that finite census.

## Limits and retained findings

The tile sampler does not cover every lawful overlapping arrangement. Some
fully pinned geometry/color combinations are outside its constructive support;
their structured rejections are not claims of semantic impossibility. Small
manual overrides and one-color requests may omit teaching contrasts. The
teaching claim applies to the tested default lesson assembly, not every override.
The positive family intentionally excludes zero-action inputs. Named negative
fixtures remain separately callable and fail validation; they are not normal
advertised textures. There is no declared cyclic teaching schedule.

The prior review index was read as a lead, not rewritten or treated as current
verification. Its unresolved baseline findings require an explicit maintainer
disposition; passing this review does not grant catalog or training approval.
The return includes all failed iterations, focused tests, source-bound checks,
independent review and a final exposed solve. `tests/test_review_contract.py`
uses portable canonical helpers and contains 67 passing cases on the final source.
## Current reviewer considerations

Source SHA-256: `f8eacbfeab97db8e356ce5baac3097de8c62a04af64168f1f3f5445fa4974297`.

# Decisions for d982cffd80f8

The supplied draw and baseline remain unchanged. The original design rationale
is unknown where the imported notes do not state it; decisions below distinguish
observed behavior from the rationale for this repair. Source identity and final
counts are recorded in `REVIEW.md` and `RESULTS.json`.

| Choice | Prior behavior | Included decision and reason | Alternative and limit |
|---|---|---|---|
| R1 validity versus difficulty | Medium generated 2–3 centers but validator required 2 | Difficulty is a sampling preference; validate the local rule family and exact requested counts | Restricting medium to 2 would hide the inconsistency by reducing lawful diversity |
| R2 colored distractions | Every nonzero cell had to belong to an isolated border | Allow touching borders, incomplete rings, nonzero centers and inert singleton colors | A global component restriction contradicts canonical evidence and confounds local filling with segmentation |
| Dimensions | Advertised endpoints could be excluded by band-specific draws | Select a feasible shape from the advertised ranges, respecting pinned dimensions | Expanding an explicitly pinned canvas would silently violate the request |
| Geometry | Random placements required one-cell separation | Construct shuffled 3-by-3 tiles with random offsets, allow touching, reserve contrast tiles when possible | Tile placement is reliable but does not span every lawful overlapping arrangement |
| Ring count | Sampled/reported count could be band constrained | Honor exact 1..6 count; unpinned difficulty weights familiar counts | Some pinned small canvases cannot support the tile request; structured rejection names only caller-supplied axes |
| Color count | Palette controls could be ignored | Realize exactly 1..6 foreground colors via ring roles, contrasts and inert pixels | A color draw without realization does not establish the observed palette size |
| Color alias | Two synonymous names presented as independent axes | `n_distinct_colors` is a supported exact compatibility alias for `palette_size` | Treating aliases as independent Cartesian dimensions creates invalid combinations and misleading envelope warnings |
| Color families | Named palettes had weak/no control effect | Warm/cool/varied choices use explicit pools; helpful texture aliases palette kind | Fixed warm/cool pools cannot realize every count up to 6; those joint requests reject explicitly |
| Unused controls | Constant position/density keys silently accepted | Remove them and reject unknown keys | Pretending they are effective would mislead curriculum callers; this is an intentional API cleanup |
| Types | Boolean/float values could pass integer-like checks | Require exact integer types for colors and integer controls | Silent coercion masks malformed training inputs |
| Negative fixtures | Named degenerate outputs mixed with normal textures | Keep legacy negative calls isolated from normal advertised valid values; reject them in self_check | Do not make a zero-action fixture count as a valid positive example merely to satisfy override machinery |
| Reference authority | Canonical labels implement simultaneous local filling | Keep Racket unchanged and pin its hash | No reference edit is justified by generator-side inconsistencies |

## Teaching contract and assembly

Default examples contain positive fills, a border with one missing or differently
colored corner, and a border with a different nonzero center. The first contrast
distinguishes cardinal-only and seven-of-eight filling; the second distinguishes
overwriting existing centers. Identity fails on positives. The executable
`CANONICAL_SHORTCUTS` registry contains the three plausible rivals that fit all
three labeled canonical pairs; `LESSON_COMPETITORS` also includes identity.
Tests and census iterate the actual declarations, not a copied inventory.

Use three demonstrations and one query. Production retains the sampled order;
rotation diagnostics hold out each of the four labeled pairs once, preserving
the remaining order. The after battery requires rotation identifiability and
the larger census uses `--per-band 100 --rotate-query`. The exact final result is
300/300 materialized lessons and 1,200/1,200 rotations with no reported ambiguity
against these finite rivals, 1,200 unique inputs and no scoring errors.

The generator does not declare a cyclic lesson schedule. The every-fifth profile
preference is a size/palette sampling choice keyed by both seed and index, not
an assertion that one fixed six-residue census exhausts all generation. Every
default input contains the needed contrasts; no claim depends on ordering a
special contrast in one particular demonstration slot. Small manual overrides
and one-color requests can reduce contrast capacity and are outside this default
assembly claim. Arbitrary unseen hypotheses remain possible.

## Canonical support and diversity

A 9-by-9, three-foreground-color preference when `(seed + sample_index) % 5 == 0`
gives repeated exact canonical-profile support. Other draws keep broad advertised
dimension and color ranges, with familiar sizes weighted. The final profile check
observed exact support in every band's 20 draws; the random gate is evidence of
those draws, not a guarantee for all seeds. The local strict-family predicate
accepts distractions allowed by the rule; it intentionally does not reintroduce
the old isolated-ring grammar under a new name.

Review found a rare palette-realization failure on a fully tiled 6-by-6 canvas.
Color roles were adjusted so the positive rings, near-ring and nonzero-center
contrast can realize six requested colors without requiring a spare outside
pixel. Regressions retain failing indices 2251 and 8152 and the forced geometry.
The independent reviewer checked 72 such palette/seed combinations and later
confirmed the final delta was alias metadata only. Broader finite probes and
their source bindings remain under `checks/code-review/`.

## Explicit support limits and rejected claims

Structured rejection describes support of this constructive sampler, not every
possible legal arrangement. For example, a fully pinned tile/color combination
can exceed available color roles even if a different unrestricted lawful drawing
could satisfy those high-level counts. Supporting the latter would require a
larger placement grammar, not silent relaxation of an exact request.

No result here measures Qwen3.5-9B accuracy or training benefit. The work removes
demonstrated data-contract failures and adds tested distinctions between named
rules. Finite-rival identifiability, morphology diagnostics, canonical-profile
support, and model-learning quality are different claims.

Both audits are findings-only. A1 reproduces an already-retained unresolved
source defect. A2 exhibits a rival surviving a documented production bound; it
does not show any generated label is wrong. Catalog approval and retained audit
resolution require explicit maintainer action outside this selected repair.

## Handoff choices

The shared runner and packager are unchanged. A standalone standard-library
compression helper lives in `checks/tooling/evidence-compression/`, with actual
CLI tests, deterministic output and raw/compressed hashes. It preserves exact
failed reports and full lesson instances within the return budget. Private solve
labels remain outside packaged evidence. The final patch is replayed in a fresh
original extraction with an independent Git root and Python environment; its
receipt, command exits and final-source equality are recorded after replay.
