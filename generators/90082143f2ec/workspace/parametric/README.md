# Native axis-policy candidate for 90082143f2ec

The root `adapter.py` and `promotion.json` now promote the retained
`axis_policy/prototype.py` programs through the native contract. The alternate
retained callable gets an explicit outer lambda/application so the native
`wrap_rule` pipeline executes it as a grid function; its rule is unchanged.
The default is returned byte-for-byte. Settings are
`{"axis_policy":"more_coherent"}` (exact canonical default) and
`{"axis_policy":"less_coherent"}`. Each setting stays fixed within an episode.
This is a reviewer candidate; owner acceptance and training admission are pending.

## Current native API and examples

`generate(seed, settings, demos=3, queries=4)` accepts exact integer seeds
0 through 2**63-1, independently supports 2–6 demonstrations and 1–4 queries,
and rejects unknown settings. Use four queries for training-shaped episodes.
The same seed gives the same inputs across settings. Per-split/per-index random
streams keep existing demonstrations and queries unchanged as counts increase.

The first two demonstrations are constructive 6×6 lessons with opposite band
orientations, equal shapes, explicit weak-line ties, and three-color weaker-axis
answers. They refute ten declared rival rules for the default and thirteen for
the alternate, including fixed axes, shape/aspect shortcuts and global fills;
alternate rivals also include highest/first-seen ties and denoising before
weaker-axis inference. This is a finite teaching check, not universal uniqueness.
Further demonstrations use 13×17, 15×14, 22×23 and 26×27 grids. Queries use 13×14,
15×15, 24×24 and 30×30 grids. Large grids contain independently placed 18% noise,
strict strong-line modes, all nine nonzero colors and noise at all four corners.
They extend only the parametric sampling domain, using fresh full-canvas content.

Python `solve()` proposes labels on this sampler's grammar; protected Racket
checks them. The exact canonical program retains its historical tie behavior.
Its selected dominant slices have strict modes here, so the helper does not
redefine canonical answers for arbitrary tied grids. The alternate program's
lowest-color tie handling is inherited unchanged from the retained sibling.

From the outer packet folder, reproduce the bounded check and examples:

```sh
WORK/.venv/bin/python review.py run python3 \
  generators/90082143f2ec/workspace/parametric/native_probe.py \
  --out ../checks/90082143f2ec/self-audit-new
```

The probe uses the same `wrap_rule` path as the native worker, and checks both
settings at seeds 0 and 17 with 2 and 6 demonstrations,
four queries, and 64 protected-Racket labels. Its example export contains one
two-demo/four-query episode per setting. `examples/public/` is a controller-side
challenge store. For actor turns use only `examples/turns/` or
`visible_turn(episode, index)`: demonstrations plus one current query, with no
future input, total count, private settings, program or query answer. First-turn
bytes match single-query generation. IDs hash exact visible bytes; duplicate
visible episodes or turns fail before creating the destination. Private records
remain in `examples/private.json`; output directories must be fresh.

The native inventory is rebuilt using `arcpuzzles parametric manifest` with
guarded replacement. Native qualification and the wrong-order causal witness
are retained in `WORK/checks/90082143f2ec/`. Production, canonical source, and
both historical prototype implementations are unchanged. The retained production
float-override API finding remains open; this native API validates exact integers.

## Historical outlier-action prototype

Status: **proposed / unapproved prototype**. The approved production generator,
canonical rule, rule hash `a86d1f36d1d2`, and canonical source SHA-256
`fce27c64e390c476ffe769e59766ad1fd179890f28233bf99a5c8176623b83e5`
remain unchanged.

## Parameter

`outlier_action` is chosen once from the episode seed and stays fixed across all
demonstrations and queries.

- `restore_mode` (default): exact canonical behavior. Determine whether rows or
  columns are the more coherent band axis, then replace each cell by that
  row/column mode.
- `mask_zero`: perform the same mode extraction, coherence comparison, and axis
  selection, but retain cells already equal to the selected line mode and replace
  outliers with `0`.

The invariant reasoning is therefore: recover row and column modes, compare their
coherence, select the stronger axis, and classify cells against its modal band.
Only the action taken on detected outliers changes.

Consecutive seeds are paired for comparison: seeds `2k` and `2k+1` receive the
same visible input grids and opposite settings. Every retained input contains
noise, so both exact Racket programs disagree on every demonstration and query.
The default command emits three demonstrations and four distinct queries for each
setting. Counts are independently configurable from 1 through 8.

## Reproduce

Run from the outer extracted packet directory:

```sh
python3 review.py run python3 \
  generators/90082143f2ec/workspace/parametric/prototype.py \
  --seeds 0 1 --demo-count 3 --query-count 4 \
  --out ../checks/parametric/90082143f2ec-outlier-action-v1

python3 review.py run python3 -m arcpuzzles check 90082143f2ec \
  --stage task_tests --phase after --timeout 600 \
  --out ../checks/90082143f2ec-task-tests-final
```

The writer refuses to overwrite an existing directory, writes public challenges
under opaque IDs derived only from visible bytes, and separates seeds, settings,
program hashes, and query answers under `private/`.

## Scope and limits

This is bounded evidence for two declared settings and the materialized seeds,
not approval or admission to the production parametric API. Identifiability is
checked against the one alternate `outlier_action`, not every conceivable ARC
program. The input sampler reuses the approved generator's lawful noisy-band
support and retries at most 64 draws per slot.

## Additional proposed sibling family

`axis_policy/` retains the incoming more/less-coherent axis capability separately from `outlier_action`. Its default is exact canonical; deterministic non-dominant mode ties apply only to alternate rules. See [its scope and commands](axis_policy/README.md). The existing outlier implementation and writer are unchanged.

The current wrapper manifest pins both families; its copied original wrapper and retained reviewer reports remain bound to their prior sources. Task-owned `../../evidence/conflict-reconciliation.json` records the manual port and bounded owner validation. All variants remain proposed and unaccepted, with training disabled.
