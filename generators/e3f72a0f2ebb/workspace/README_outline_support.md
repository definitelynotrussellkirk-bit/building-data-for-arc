# Outline support probe

`probe_outline_support.py` is an executable authoring probe for the adjacent
selected generator. It reads labeled canonical examples, so keep it closed
during visible-only solving. It uses the local `reviewer_support.find_root` and
`canonical_pairs` helpers in either a library or a copied runtime. It does not
import a sibling checkout or private reference-runner functions.

From the packet's `WORK` directory:

```bash
python3 run_with_racket.py python3 generators/e3f72a0f2ebb/workspace/probe_outline_support.py --racket-witnesses --out ../checks/support-probe.json
```

The wrapper changes the actual working directory to `WORK/repo`. The report
records that directory, the payload argv, Python version, generator/probe/helper
hashes, canonical record/rule hashes, and imported local Python source hashes.
Use a **new output path** on every run. Publication is atomic and cannot replace
an existing file. Inspect `status`, `summary`, and the completed denominators;
exit 0 alone is not the evidence. Exit codes are 0 for `no_findings`, 1 for
retained findings, and 2 for execution or reporting errors.

## What the default run measures

- Direct generation at seeds 0 through 15 and indices 0 through 63, with each of
  `easy`, `medium`, and `hard` passed explicitly: **3,072 draws**. This is the
  pre-materialization population, with no rejection resampling or deduplication.
- Every advertised joint integer tuple for grid height, grid width, component
  count, and distinct-color count, at seed 0 and indices 0 through 3 in every
  band. For the 7..18, 8..18, 2..4, and 1..4 domains, this is **14,256 compatible
  draws plus 4,752 incompatible requests**. The incompatible cases must reject
  because the color count exceeds the component count. Each compatible request
  must construct its exact observed counts and pass the validator.
- Independent same-color 4-connected components, tight bounding-box frames,
  shape and palette diversity, identity components, repeated colors, additions,
  interior deletions, and frame/bounding-box interference. Counts include exact
  unique inputs, input-hash digests, and index-residue breakdowns. Every generated
  grid must contain a component requiring both additions and deletion.
- Canonical profiles are measured in two explicitly different ways.
  `canonical_profile_count_hits` matches height, width, and total palette
  cardinality, including zero when present, following the shared profile-floor
  convention. `exact_canonical_dimension_color_set_hits` additionally requires
  the actual nonzero color set of a labeled canonical input. Equal-cardinality
  palettes with different colors can match the first metric without the second.
- Every actual entry in `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, preserving
  its declaration namespace. Every claimed canonical shortcut is checked against
  **all labeled canonical pairs**. Generated rival agreement/refutation counts
  use the independent Python frame prediction; exact first refutations are saved.
- With `--racket-witnesses`, up to **64 exact retained inputs** are labeled by
  `Catalog(root).apply(..., reference="canonical")`. The full public API receipt,
  actual labels, individual errors, and source/rule bindings are retained and
  checked. Without this flag, generated predictions are explicitly Python-only.

All failed cases keep their replay settings and, when available, exact inputs and
outputs. Successful cases are compacted into counts, complete-population digests,
and at most 64 representative witnesses. An ordinary successful report is small;
a large failure population is intentionally not truncated.

These measurements do not establish lesson identifiability. Use the shared
`arcpuzzles lesson-census` command for production lessons and query rotations.
The probe records both canonical profile hit frequencies without assuming
that a small diagnostic draw set must contain every feature. Finite fixed seeds
also do not exhaust random support. The reference rule is pinned to unchanged
`8d3a7f6a327b`; collisions are domain findings, and Python paint order is not
assumed authoritative when frames overlap.

## Small checks and custom populations

The independent analysis has seven hand-written self-tests, including a
same-cardinality/different-color-set profile example:

```bash
python3 generators/e3f72a0f2ebb/workspace/probe_outline_support.py --self-test
```

To inspect one direct draw and canonical acceptance without exhaustive overrides:

```bash
python3 run_with_racket.py python3 generators/e3f72a0f2ebb/workspace/probe_outline_support.py --band medium --seed-start 503 --seeds 1 --index-start 26 --indices 1 --skip-joint --out ../checks/support-one-draw.json
```

Use `--joint-seed-start`, `--joint-seeds`, `--joint-index-start`, and
`--joint-indices` to expand the constructive support population. All four
schedule residues are the normal override default. A plain runtime supports
Python analysis; optional Racket labels require a library or the public-library
mirror supplied by the task-test snapshot. Missing support is reported as an
error, never satisfied by borrowing an external checkout.
