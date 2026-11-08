# Diagonal radius and propagation through surviving stamps

The native family builds on the retained radius prototype. `prototype.py` and
its older probe/tests remain unchanged; `family.py` reuses its exact radius-2
program and Python stamp implementation. The production generator remains
version 2.0.0 with its existing canonical approval.

| Setting | Meaning |
| --- | --- |
| `diagonal_radius: 1` | Four green stamps at offsets `(±1, ±1)` |
| `diagonal_radius: 2` | Four green stamps at offsets `(±2, ±2)` |
| `propagation_passes: 1` | One sweep over the original blue markers |
| `propagation_passes: 2` | Complete the first sweep, then start a second sweep from its surviving green marks |

The Cartesian family has four settings. The default `(radius=1, passes=1)` is
the exact 1,355-byte canonical Racket source. A sweep discovers its blue markers
once, in row-major order. Each marker paints its entire row and column blue,
its center red, then its in-bounds diagonal stamps green. Later markers may
overwrite earlier centers or stamps. Nothing rescans newly painted blue cells
within that same sweep.

For the second sweep, every surviving green cell in the completed first grid
becomes a blue marker on the **original background color**; all other cells
are reset to that background. The same radius-specific sweep then runs on
this derived seed grid. This is distinct from repeating on the first output,
propagating its blue cross cells, or taking every nominal diagonal position.
Cross overwrites can erase would-be seeds, making the intermediate state
necessary to determine where the second sweep begins.

## Grammar and teaching

Native inputs contain one background from `{0,4,5,6,7,8,9}` and 2–12 distinct
blue markers. Original marker rows and columns may coincide or be adjacent;
markers may touch edges. These are deliberate extensions of the production
sampler's spacing/count/size restrictions, while the default Racket program
itself is unchanged. Output order is row-major after any sampled input rotation;
the family does not claim rotation-equivariant overwrite semantics.

Two constructive demonstrations establish the setting before any query. The
first uses a diagonal chain on 11×13; later crosses erase earlier stamps,
and green stamps overwrite later queued markers for both radii. Those original
markers must still execute even when their current cells are no longer blue. The second uses shared rows/columns and clipped
boundary stamps on 9×11. The first background is zero, the second nonzero.
Coordinates, backgrounds and whole-grid dihedral transforms vary with seed.
Additional demonstrations extend marker counts and geometry, up to 26×28.

The four query roles are 7×9 with 3 markers, 17×21 with 6, 30×30 with 12,
and 27×24 with 9, up to transposition. Query roles are shuffled by a separate
seed stream. Larger scenes distribute markers across the canvas, retain
interactions and boundary contacts, and create long crossing lines and dense
outputs. They are not small scenes placed in larger empty padding.

`generate(seed, settings, demos=3, queries=4)` returns native `train`, `test`
and `program_solution`. Seeds are exact integers `0..2**63-1`, demos 2–6,
queries 1–4. Inputs match across all settings, and increasing either count
preserves the corresponding prefix. No query answer becomes a later demo.
Python output labels are deterministic claims; native qualification independently
executes the exact programs through protected Racket.

## Reproduction and reusable audit

From the outer packet, using its ready Python:

```bash
WORK/.venv/bin/python review.py run python3 generators/7355dc4aa5e5/workspace/parametric/audit.py --out ../checks/7355dc4aa5e5/self-review.json
WORK/.venv/bin/python review.py task-tests 7355dc4aa5e5 --phase after --out ../checks/7355dc4aa5e5/task-tests
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 7355dc4aa5e5 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/7355dc4aa5e5/qualification --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/7355dc4aa5e5/qualification/qualification.json --out ../checks/7355dc4aa5e5/preview
WORK/.venv/bin/python review.py preview-public verify --bundle ../checks/7355dc4aa5e5/preview
```

Use fresh output paths when reproducing retained checks. Build the source
inventory first with native `parametric manifest`, declaring the compact
`evidence/current` receipts and focused tests. The independent `rivals.py`
and `audit.py` check event-order semantics and demonstration-only support
against explicit executable alternatives. Finite checks do not establish
uniqueness against every imaginable rule or measured model learning.

The older `prototype.py --base-seed ... --out ...` probe still describes its
original three-demo/one-query radius-only experiment. Its previous evidence
must not be substituted for current native qualification, and its multi-query
containers must not be presented as a sequential solver turn.

## Visibility and acceptance

The bundled native preview emits a separate, exact-byte-hashed public file
for each selected query, containing only the original demonstrations and that
query input. Give a solver one selected file per turn. Keep directory listings,
future query files, ordering, settings, programs and answers with the controller.
There are no total-count or final-turn hints; the first view is the same as
single-query use.

This is a reviewer-ready proposal only after its retained qualification and
causal replay pass. The owner must separately qualify and freshly accept the
exact integrated sources. Public serialization checks do not rerun Racket or
grant acceptance. No training admission or consumer activation is implied.
