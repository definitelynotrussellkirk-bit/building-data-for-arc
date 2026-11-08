# Proposed parametric rule: fallback panel

This task-local prototype keeps the production generator and canonical authority
unchanged. It varies one episode-wide rule parameter:

- `fallback_panel = left` (**canonical/default**): when any aligned panel cell
  pair overlaps or is empty on both sides, return the complete left panel.
- `fallback_panel = right` (**proposed**): perform the same global
  zero-complement test and the same successful overlay, but return the complete
  right panel when the test fails.

The invariant reasoning is unchanged: split at the gray separator, test all
aligned pairs globally, overlay only for exact zero-complements, otherwise copy
one fixed panel. The setting is selected once from the episode seed and remains
fixed across every demonstration and query. Paired seeds `2k` and `2k+1` use
the same `input_seed = k`, so their visible inputs and ordering are identical
while only the hidden rule setting changes. Four demonstrations and four queries
each cover complement, overlap-only, gap-only, and balanced overlap-plus-gap
inputs; the demonstration and query splits are independently shuffled.

## Exact replay

From the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/27080597d778/workspace/parametric/prototype.py \
  --out ../checks/parametric/fallback-panel-final \
  --seeds 0 1 --difficulty medium --start-index 0 --n-train 4 --n-test 4
```

Focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/27080597d778/tests/test_parametric_fallback_panel.py
```

Bounded adversarial audit (public/private export plus a real-Racket rule matrix):

```bash
python3 review.py run python3 \
  generators/27080597d778/workspace/parametric/audit.py \
  --evidence ../checks/parametric/fallback-panel-final \
  --out ../checks/parametric/fallback-panel-adversarial.json \
  --input-seeds 0 1 2 --sample-indices 0 1 2 3 4 5 6 7 \
  --difficulties easy medium hard
```

The writer obtains every label from the bundled Racket runtime, checks an
independent Python mirror, replays all nine canonical pairs under the exact
canonical default, and writes exact rules plus private evidence. Public filenames
are `challenge-<sha256>.json`, where the hash covers only canonical visible demo
pairs and query inputs. Hidden settings, seeds, programs, and query answers stay
under `private/` and `rules/`.

This is a **proposed prototype**, not a production parametric API, a canonical
rule change, training admission, or approval of the right-fallback setting.
