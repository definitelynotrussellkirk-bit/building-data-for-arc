## ef65ec3491d7

**Findings-only audit: two reproduced issues; selected source unchanged.**
The inspected generator is version `2.1.0`, source SHA-256
`121d495b393e701d825faf99c9d7cc825fb4e53a1f318752b161f26f0a399c3e`.
The selected Racket rule executed with hash `8897bd11bd68`, matching the catalog;
its full normalized SHA-256 is
`8897bd11bd68aaaaca09e657ed0efdcec4f199546a3c10c6de45482308c68b8f`.
The execution receipt's exact rule-text SHA-256 is
`2cf42abebd7fd1eb8094f7ad89e2f14d5bdc75435ea41e135833485fc46760dd`.
Current `notes.md` contains only its introductory placeholder, and
`evidence/review_index.json` is absent. No prior-source solve or private solve data
was consulted.

| Finding | Classification | Reproduction | Patch status |
| --- | --- | --- | --- |
| A-ef65-1 | Canonical coverage gap and unrefuted first-seed rival | Canonical query has two different seeds in one room; retained normal generated examples have at most one. Rival agrees on 30/30 generated inputs and 4/4 canonical training pairs, but differs from Racket on 8 query cells. | Findings only; no source changes |
| A-ef65-2 | Ignored declared palette/texture overrides | Seed 42000, sample index 1, easy: six different declared override settings all return the same input with two seed colors. | Findings only; no source changes |

### A-ef65-1: Normal generation excludes a canonical multi-seed room

The normal generation branch places zero or one seed in each room. Its fallback
only seeds a room if every interior cell is still zero. Consequently, this family
cannot expose interactions between differently colored seeds in the same room.
The canonical labelled query, `canonical.v0.test.0`, contains exactly that case:
one chamber contains color 4 at `(6, 4)` and color 6 at `(6, 8)` (zero-based).
Its input is 10 rows × 13 columns, and its output is 10 rows × 13 columns.
Input SHA-256:
`1f66772853453a254785400fd18af90920dd9d71c9d3cbba7d471e4349e14368`.

The deliberately specified rival preserves all original seeds and fills every
zero in a non-wall connected chamber using its first seed in row-major order.
It matches the selected Racket output on all four canonical training pairs and
all 30 retained normal generated inputs. It fails on the canonical query:
Racket fills the eight initially empty cells of the two-seed chamber with color
6, while this rival fills them with color 4. The differing coordinates are
`(6,5)`, `(6,6)`, `(6,7)`, `(7,4)`, `(7,5)`, `(7,6)`, `(7,7)`, `(7,8)`.
Both rules preserve the original seed cells.

The canonical witness passes the selected generator's `self_check`, and public
`arcpuzzles apply --check-generator-domain` reports it valid. It is a lawful
canonical input accepted by that validator, while lying outside the normal
generator's documented one-seed-per-room subdomain. All 35 retained reference
outputs are valid, and Racket matches all 5/5 canonical labelled outputs.
The finding concerns missing canonical coverage and examples that cannot
distinguish this specific rival. It does not establish a failure of any retained
generated label or a universal identifiability result.

Evidence: `checks/audit/ef65ec3491d7/findings.json`, `witnesses[0]`, contains the
exact input, actual Racket output, rival output, differing cells, and validator
result. `racket.json`, `results[4]`, is the independently executed reference
receipt. The rival and deterministic preparation are in `probe.py`.
The witness is canonical, so generator seed/index/overrides are explicitly null;
the generated comparison cases retain their exact seed/index/difficulty.

Suggested maintainer action: add normal examples with differently colored seeds
sharing a chamber and explicit examples that reveal the selected overwrite
behavior, including color orders that do not turn the outcome into a numeric
maximum-color shortcut. Keep the selected reference rule authoritative.

### A-ef65-2: Palette and helpful-texture overrides have no effect

At `generate(42000, 1, difficulty="easy", ...)`, these six settings each produce
the same byte-identical input as the unoverridden call:

- `palette_kind="warm"`
- `palette_kind="cool"`
- `palette_size=1`
- `palette_size=8`
- `texture="warm"`
- `texture="cool"`

Every output is accepted by `self_check` and contains exactly two seed colors,
`{1, 3}`. Thus the requested palette sizes 1 and 8 both realize 2. The input
SHA-256 is `2330a261a5900d4746b66ed7c4859ea4b302ab07b26b4fd22f06b1eface2de57`.
These values are declared in `AXES`/`HELPFUL_TEXTURES`. Source inspection confirms
that normal generation never consumes `palette_kind` or `palette_size`, and
`texture` affects only the separate degenerate branch. The guide's texture
contract explicitly identifies an identical un-textured draw as a dead branch.

Evidence: `probe.json` and `findings.json`, `override_probes`, retain all six calls,
realized seed-color counts, input hashes, and validator results. Their identical
input is retained as `generated.easy.1` at `inputs.json[6]`; `racket.json`,
`results[6]`, supplies its actual selected-rule output and valid-domain receipt.
Suggested maintainer action: implement the declared controls with observable
semantics, or remove unsupported controls from the declared interface.

### Exact scope, commands, and limits

The bounded comparison covers all 5 canonical pairs and 30 normally generated
inputs: easy seed 42000, medium seed 42001, hard seed 42002, each with sample
indices 0–9 and no overrides. All 30 pass `self_check`; none contains multiple
seeds in a non-wall region. One deliberately specified rival was evaluated.
Six override calls were compared at the one documented seed/index above.
No full battery, task-test stage, lesson census, query-rotation census, or
degenerate-texture sweep was run. The source declares no `LESSON_COMPETITORS`
contract, and this audit makes no lesson-level aggregate pass claim.

`checks/audit/ef65ec3491d7/commands.json` records exact wrapper commands, working
directories, exit codes, and evidence paths. Public Racket apply exited 0 on
35/35 inputs, each with valid output and valid generator-domain status.
The successful comparison exited 0. The first analysis attempt failed because
the audit helper compared a full SHA-256 to the runtime's 12-character rule hash;
that helper revision and failure remain in `probe-v1-hash-assumption.py` and
`analysis.log`. The corrected helper compares the documented prefix and its
successful run is retained in `analysis-v2.log`; no reference rerun was needed.

The audit leaves the generator, canonical ledger, selected authorities, and
associated task sources unchanged. Findings remain open for maintainer review.
