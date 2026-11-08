# Native promotion: count, segment, render

The new `adapter.py` exposes the existing three exact fill-order programs plus
`largest_component_count`. That fourth policy measures monochromatic cardinal
cyan components, selects their maximum size, and applies the canonical quarter-
count glyph renderer to that input-dependent integer. Its companion wrong-
intermediate program substitutes the global cyan count. This is contextual
selection plus aggregation, not an iterative simulation claim.

The **native API supports 4–6 demonstrations and 1–4 queries**; ordinary
qualification uses four. The first three show q1/q2/q3. They deliberately fit
both counting policies, and a held-out query separates those policies. Demo four
repairs this concrete ambiguity. A narrower minimum is used rather than claiming
an unidentifiable 2–3-demo lesson is ready. The legacy prototype below keeps its
old API and is not the new native export interface.

Inputs are setting-independent. Four queries are constructed before slicing;
changing demo count does not change the query bank. Use `preview-public export`
for private seeded shuffling of all four queries before single-turn selection.
`public_turn` is a strict one-query projection, not a presentation controller.

The opt-in native input grammar extends the old {0,8} grid to arbitrary noncyan
clutter, ignored by both rules. Signal is 4–19 cyan cells: the exact canonical
program returns an empty tile above count 19, so a dense cyan stress case would
leave the original counting domain. The 30x30 query instead distributes 19
signal cells across three corners (all four borders) among at least 181 noncyan
distractor cells. Its answer remains 5x5; density and size claims concern inputs.
Largest-component query counts span q1/q2/q3; the full q4 glyph remains exercised
in the global-count settings. Programs are total outside this sampled subgrammar,
but unsampled domains are not claimed as qualified teaching curricula.

Run from the packet root:

```sh
python3 review.py run python3 generators/5dc10de63325/workspace/parametric/audit_native.py --seeds 16 --out ../checks/5dc10de63325/new-audit.json
python3 review.py task-tests 5dc10de63325 --phase after --out ../checks/5dc10de63325/new-tests
python3 review.py run python3 -m arcpuzzles parametric qualify 5dc10de63325 --out ../checks/5dc10de63325/new-qualification --summary
```

The audit compares 581 analytical policies (24 glyph orders, six count metrics,
four rounding policies, and five constants), then executes 42 labels through
protected Racket. These are bounded checks, not universal identifiability.
Source-bound native qualification and causal replay are separate evidence.
Production generator, canonical ledger and legacy prototype are unchanged.

---

# Fill-order parametric prototype

This is an **isolated proposed prototype**, version `fill-order-v2`. Production
`generator.py`, the canonical Racket rule, and approval state are unchanged.

## Parameter and supervision

`fill_order` is selected once from the deterministic episode seed:

| Setting | Order within the 2×2 glyph |
| --- | --- |
| `bottom_row_first` (canonical/default) | bottom-right, bottom-left, top-right, top-left |
| `right_column_first` | bottom-right, top-right, bottom-left, top-left |
| `top_row_first` | top-left, top-right, bottom-left, bottom-right |

Every setting counts cyan cells, floor-divides by four, fills that many cells
in a 2×2 glyph, and repeats it around the central zero cross. The default
materializes to the exact pinned canonical source bytes.

The first three demonstrations have cyan counts **7, 11, 15**. They identify
the fixed fill order and distinguish floor division from ceiling, nearest
quarter, and a two-glyph threshold. The previous counts 5, 9, 13 allowed a
nearest-quarter rival that disagreed on the previous count-10 query. The new
four queries have counts **6, 10, 14, 18** and distinct lawful input grids.

`--train` and `--test` are independent: 3–32 demonstrations and 1–32 queries.
Additional pairs cycle those respective count schedules with varied geometries.
Every input is checked with the selected generator's grammar; exact duplicate
inputs are rejected with a 100-attempt limit per pair, followed by an explicit
error rather than a shortened lesson. Fewer than three demonstrations are
unsupported because this prototype guarantees q1/q2/q3 witnesses.

The input RNG seed is independent of the hidden setting. The evidence builder
uses the same `--input-seed` across all three settings, so paired comparisons
have identical inputs and ordering. `build_episode` additionally accepts
`seed`, `input_seed`, `n_train`, and `n_test`; when `input_seed` is omitted it
uses `seed`. Hidden parameters remain fixed across the complete episode.

Every label and all three setting predictions are executed through matching
Racket. A Python mirror checks parity. The identifiability check first filters
100 analytical rivals using demonstrations alone: all 24 fixed glyph orders
combined with floor, ceiling, nearest-quarter, and two-glyph count policies,
plus four constant outputs. It then checks every query against all surviving
rivals. These are finite declared rivals, not a universal uniqueness proof.

## Reproduce four-query evidence

From the outer extracted packet directory, with a Python environment containing
NumPy and Pillow (the packet setup supplies Racket):

```bash
PATH="$PWD/WORK/.venv/bin:$PATH" WORK/.venv/bin/python review.py run python \
  generators/5dc10de63325/workspace/parametric/prototype.py \
  --train 3 --test 4 --input-seed 2026 \
  --out-dir ../checks/5dc10de63325/fill-order-v2-replay
```

The builder refuses to overwrite an existing output directory. An independently
sized runnable example uses `--train 5 --test 2 --input-seed 17`.

Outputs include a summary and hash manifest; one public challenge per setting;
private episodes, rival predictions, source hashes and runtime identity; and
exact materialized Racket programs. Only `public/` is intended for solving.

Public files contain exactly `train` input/output grids and `test` input grids.
Their bytes are `reviewer_support.public_challenge_bytes(episode)`, and their
opaque filenames are `challenge-<public_challenge_id(episode)>.json`. Both writer
and identifier use that same visible projection. Metadata anywhere in a pair,
settings, seeds, prototype versions and query answers cannot affect the public
name or bytes. Batch descriptors are sorted by the public content ID, and
duplicate visible payloads raise before an existing public file can be replaced.
Original retained galleries remain historical evidence; this
format intentionally removes their task/schema/version envelope.

Focused regression tests (payload paths relative to `WORK/repo`):

```bash
WORK/.venv/bin/python review.py run python -m pytest -q \
  generators/5dc10de63325/tests/test_parametric_fill_order.py \
  generators/5dc10de63325/tests/test_parametric_public_names.py \
  generators/5dc10de63325/tests/test_parametric_four_queries.py
```

Retained current execution evidence is under `WORK/checks/5dc10de63325/`.
The tested maximum 32/32 request checks input uniqueness only; retained Racket
exports exercise 3/4 and 5/2 counts, one episode per setting per export.
This prototype does not enter the production parametric API, approve rule
variants, clear production lint findings, or admit data to training.

## Disjoint union candidate

Five disjoint exact rules now share cyan-component and four-marker scenes: the three prior fill orders, largest-component count, and bucket-color relay. The four-demo minimum is preserved. Component sizes, total counts, selected marker colors and query order vary. Thirty-by-thirty scenes span the full canvas while respecting the lawful sparse 4..19-cyan and exactly-four-marker domain. Original samplers remain available; candidate tests cover both authored rival sets and fixed-value proxies. Owner qualification and acceptance remain separate.
