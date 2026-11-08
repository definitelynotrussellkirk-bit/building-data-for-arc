# Native marker-lattice family

This task-local adapter exposes `lattice_rule` with three episode-fixed values.
It preserves the canonical generator and its authority. Reviewer qualification
is separate from owner acceptance and from any training admission.

| Setting | Executed rule |
|---|---|
| `period2` (default) | Exact canonical source: fill zero cells sharing both marker-coordinate residues modulo 2. |
| `period3` | The retained prototype's same transformation modulo 3. |
| `ray_size` | Find the first gray cell strictly east of the marker, recover its entire four-connected gray component, and use period 2 for even area or period 3 for odd area. |

Every rule preserves gray blockers and every nonzero cell. The sequential
variant's selected object can differ from the largest, nearest, earliest in
scan order, or last ray-hit object. Its cell count can differ from ray length,
bounding-box area, and eight-connected size. The Racket resource handles an
empty east ray with period 2, although generated lessons always contain a hit.

## Native interface and teaching

`adapter.program(settings)` returns exact Racket source.
`adapter.generate(seed, settings, demos=3, queries=4)` returns private labeled
`train`/`test` pairs and `program_solution`. Seeds are literal integers in
0..2**63-1. Independent limits are 2–6 demonstrations and 1–4 queries; use
three/four for normal training. All inputs in one lesson are distinct.

The first two demos construct opposite selected-component parities. A bounded
64-candidate-per-slot selector chooses demonstrations that reject the 14
structural shortcuts reproduced during self-review, using demonstration labels
alone. It never inspects queries. Three-or-more-demo lessons use matched input
selection across all three settings. At two demos, selection can differ by
setting; query inputs remain matched. This is an explicit tradeoff to teach the
finite rivals within the two-demo limit. Failed selection raises an error; no
short lesson or silent relaxation is returned. Two-demo lessons keep the marker
color fixed, while longer lessons demonstrate colors on both sides of gray-5.

Query profiles are 9×9, 15×17, 21×24, and 30×30. Gray distractors and active lattice
cells span the canvas. These are separate parametric-family geometry extensions;
the production generator retains its original three canonical profiles.

`adapter.public_challenge(episode, query_index=i)` exposes the fixed
demonstrations and exactly query i. Its first-turn bytes equal a separately
requested single-query episode. Full four-query exports are controller assets;
only one turn file should be given to the model. Programs, settings, answers,
future queries, and future-query counts remain private. Public filenames are
full SHA-256 hashes of exact `reviewer_support.public_challenge_bytes` output.

## Reproduce the bounded audit

From the packet root, using the interpreter that passes `python-check`:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/c9034f0626e0/workspace/parametric/audit_native.py \
  --out ../checks/c9034f0626e0/new-audit
```

Use a new destination. The tool independently executes every retained label and
its finite Racket rival bank, checks demonstrations before queries, retains
ambiguities/errors explicitly, and writes public full challenges, separate turn
files, private source snapshots/labels, runtime identity, and compact metrics.
No acceptance state changes. `rivals.py` supplies a separate Python rival bank
for bounded demonstration selection and reproductions.

Focused tests and native qualification:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/c9034f0626e0/tests/test_native_parametric.py \
  generators/c9034f0626e0/tests/test_parametric_lattice_period.py \
  generators/c9034f0626e0/workspace/parametric/test_native_audit.py
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  c9034f0626e0 --out ../checks/c9034f0626e0/new-qualification --summary
```

The manifest must bind the current sources first. The owner re-qualifies and
accepts the exact integrated bytes through the documented native API.

## Preserved legacy prototype and limitations

`prototype.py` still supports its original `lattice_period` 2/3, three-demo,
one-query evidence builder; the native adapter reuses its rule materialization
and mirror. Its public writer has been corrected to canonical visible-byte
hashes. Old evidence directories remain historical and are not current proof.

Finite rival checks do not establish universal rule uniqueness or measured
learning benefit. Teaching is ordered; arbitrary demonstration/query rotations
are not promised, especially for two-demo `ray_size` lessons. Count-boundary,
large-grid, and public-projection checks are bounded evidence, not an exhaustive
proof over all seeds. The canonical rule and production approval are unchanged.
