# Proposed swap-scope parameterization

Status: **proposed task-local prototype**, separate from the approved canonical
generator. It does not change production generation, the canonical Racket rule,
review status, or training admission.

## Parameter

`swap_scope` is chosen once per episode and held fixed across every demonstration
and query.

| Value | Behavior |
|---|---|
| `interior` | Canonical/default: locate the sole gray frame and swap the two interior role colors only in its strict interior. |
| `exterior` | Alternate: infer the same two colors from the frame interior, then swap them only strictly outside the frame rectangle. |

Both settings preserve the frame, background, object roles, color pair, and the
need to distinguish the marked region from same-color clutter. The alternate
changes only the spatial predicate controlling where the same color exchange is
executed. Every generated input contains both colors inside and outside, so one
labeled demonstration already separates the two settings; the default command
uses two demonstrations and four distinct queries.

The exact canonical program is materialized as `rules/interior.rkt`.
`rules/exterior.rkt` is derived by replacing the canonical strict-interior
predicate with the strict-exterior predicate. The executable verifies this exact
derivation and the canonical normalized rule hash before use.

## Run

From the outer packet directory containing `review.py`:

```bash
python3 review.py run python3 generators/51e59bb53cac/workspace/parametric/prototype.py \
  --seed 17 --swap-scope both --demos 2 --queries 4 \
  --out ../checks/parametric/swap-scope-seed17

python3 review.py run python3 -m pytest \
  generators/51e59bb53cac/tests/test_parametric_swap_scope.py -q
```

`--demos` and `--queries` are independent integers in `1..32`; the sampler
fails rather than duplicating or omitting requested inputs. `--swap-scope auto`
chooses a setting deterministically from the seed before any input draw. Explicit
settings and `both` support controlled comparisons on the same input sequence.

## Evidence and privacy boundary

All demonstration and query labels execute the matching materialized Racket
program. A Python mirror is checked independently. For each query,
`identify_query(demonstrations, query_input, engine=...)` fits the two settings
plus global-swap and identity rivals using only demonstration inputs/outputs; it
accepts neither the hidden selected setting nor a query answer.

Only `OUT/public/*.json` are public challenges. Each file contains exactly
visible demonstration inputs/outputs and query inputs. Its full SHA-256 filename
is computed from those exact public bytes; settings, seed, query answers, rule
text, and ordinals cannot affect the public identifier. Multi-setting batches are
written and reported in public-ID order, never hidden-setting order. All private metadata,
query labels, rules, setting maps, execution logs, and the parameter witness live
under `OUT/private/`. `summary.json` is reviewer evidence, not a public challenge.

## Limits

This is bounded evidence for the current canonical generator domain (8..22 per
side) and recorded seeds. Declared-rival identification is finite, not a proof
against every possible rule. Successful tests do not approve the alternate rule
or admit its examples to training.
