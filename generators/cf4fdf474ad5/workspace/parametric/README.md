# Proposed height-threshold parameterization

**Status:** task-local proposed prototype. The selected `generator.py`, exact
canonical authority, `RULE_HASH`, approval state, and training admission are
unchanged.

## Parameter and rule

One hidden `max_height` value is fixed for the whole episode:

| Value | Behavior |
|---|---|
| `5` | Keep only patches at most five rows high, then apply the canonical green-count, smaller-area, top-left ordering. |
| `8` | Exact canonical/default program bytes. |
| `9` | Admit the normally invalid nine-row patch, then apply the same ordering. |

The approved four-patch sampler is reused only for inputs. Every sampled scene
contains heights 5, 8, and 9 with increasing winning green counts, so one
labeled demonstration distinguishes all three declared settings. The sampler is
setting-neutral: the same seed and demo/query counts produce identical visible
inputs for every setting. Demonstration and query streams are separate, so each
stream's prefix is stable when the other count changes.

`adapter.py` plus `promotion.json` implement the native promotion contract for
1–16 demonstrations and 1–16 queries independently. Python labels are claims;
owner qualification must re-execute them. This prototype does not alter or
approve production behavior.

## Focused tests

From the extracted packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/cf4fdf474ad5/tests/test_parametric_height_threshold.py
```

The tests cover exact canonical bytes, strict validation, explicit height-5/8/9
boundaries, all canonical labels through Racket, deterministic setting-neutral
sampling, count extrema, stream-prefix independence, finite-setting
identifiability, adapter/contract shape, visible-ID invariance, duplicate-public
rejection, and protected-Racket evidence writing.

## Materialize retained evidence

Use a new output directory:

```bash
python3 review.py run python3 \
  generators/cf4fdf474ad5/workspace/parametric/prototype.py \
  --seed 0 --seed 1 --seed 2 --demos 1 --queries 4 \
  --out ../checks/parametric/height-threshold-v1

python3 WORK/check_public_exports.py \
  WORK/checks/parametric/height-threshold-v1/public --demos 1 --queries 4
```

The CLI verifies all three Racket programs on every demonstration and query,
requires the chosen setting to be the sole demonstration survivor, requires all
four queries to differ under both rival settings, and checks every chosen label
against the independent Python mirror before writing anything.

Only `public/<visible-bytes-sha256>.json` is model-visible. It contains
labeled demonstrations and masked query inputs. `private/` retains settings,
query answers, exact programs, source hashes, finite-rival certificates, and
protected runtime identity. Filenames and bytes are derived solely from visible
content; changing a setting, program, seed, or query answer cannot change them.
Duplicate visible payloads and existing destinations are refused before write.

## Limits

The prototype covers the selected generator's reviewed 22–28 square/rectangular
four-patch subdomain. It does not claim arbitrary component shapes, missing
height classes, or thresholds other than 5, 8, and 9. Finite identifiability is
against these three declared programs, not every imaginable rule. Retained
Racket evidence is bounded to its recorded seeds and counts and is not owner
acceptance or training admission.
