# Proposed `depth_policy` prototype

This directory contains finite, executable review evidence for a **proposed,
unapproved** parameterization of crossing-bar task `2f0a4d589c58`. It does not
change `generator.py`, the canonical ledger, or production task authority.

## Parameter

`depth_policy` is sampled once per episode and remains fixed across all three
demonstrations and the held-out query.

| Value | Overlap in each output |
|---|---|
| `toggle` (default) | Give the overlap to the bar that was behind in the input. |
| `horizontal_front` | Give the overlap to the horizontal bar. |
| `vertical_front` | Give the overlap to the vertical bar. |

The `toggle` program is the canonical Racket source byte-for-byte. The two
alternative settings replace exactly one guarded overlap expression. Input
constraints do not depend on the setting.

Each episode uses four authored lawful crossing-bar inputs. The three visible
demonstrations include both possible input occluders, so every declared rival
that changes the query is already refuted in the demonstrations. All retained
labels and rival predictions are executed by the protected Racket bridge;
`python_apply` is an independent assertion oracle only. Public episode files
contain visible train labels but mask query outputs. Private files retain the
selected rule, query labels, and rival evidence.

Run from the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/2f0a4d589c58/tests/test_parametric_depth_policy.py

python3 review.py run python3 \
  generators/2f0a4d589c58/workspace/parametric/prototype.py \
  --out ../checks/parametric/depth-policy-v1
```

The output directory must not already exist. Evidence is intentionally finite:
four fixtures and one representative seed per policy. It is not a distribution
claim, approval decision, or replacement generator.
