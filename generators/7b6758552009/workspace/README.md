# Replay tools and next-agent entry point

`../generator.py` is the selected implementation. `probe_palette.py` is a
read-only, source-bound diagnostic tool; it does not install a generator or
change canonical authorities.

## Run from the original extracted packet root

```bash
python setup_racket.py
python run_with_racket.py python -m pytest -q generators/7b6758552009/tests
python run_with_racket.py python generators/7b6758552009/workspace/probe_palette.py \
  --samples 200 --audits --out ../checks/probe-replay
python run_with_racket.py python -m arcpuzzles generate 7b6758552009 \
  --count 3 --seed 20260928 --difficulty medium --train 4 --test 2 \
  --allow-unapproved --out ../checks/episodes-replay.private.jsonl
```

Output paths must not already exist. Outside a review packet, configure Racket
normally and run the same Python commands from the repository. The probe uses
an isolated copy produced by `Catalog`/`prepare_runtime`, then the actual
protected Racket bridge and existing rule wrapper. It never uses a Python
mirror as the label authority. It records source, rule, runtime and canonical
ledger hashes. Translation and bijective color-renaming are checked against
Racket. `--help` requires no Racket startup; `--samples 0` is rejected.

The baseline defaults to the immutable assignment snapshot when available;
otherwise only the current version is checked. `--baseline /path/generator.py`
can explicitly supply the previous selected version. The `--audits` option is
specific to the pinned audit targets `410efa4c3988` and `c47d6176a161`; inspect
recorded hashes before comparing a different source revision.

## Outputs

`summary.json` contains measured coverage and oracle comparisons.
`witnesses.private.json` contains exact seeds, inputs, reference outputs and
rival outputs. `challenges.jsonl` omits reference answers but retains diagnostic
rival names in its IDs, so it is a debugging artifact, not a blinded benchmark;
some witnesses refute multiple rivals and therefore repeat an input. For blind
solver testing use the neutral IDs and query-input-only episodes in the review
return's `checks/integration/episodes.public.jsonl`. Do not expose private
outputs, programs or semantic witness IDs to a candidate solver.

`audit_findings.json` distinguishes ordinary generated examples, lawful manual
counterexamples, out-of-grammar checker probes, and forced fallback execution.
Errors are written to `failure.json`; a failed run is not overwritten.

## Override contract (3.0.0)

| Axis | Accepted values |
|---|---|
| `grid_h` | integers 6 through 12 |
| `grid_w` | integers 10 through 18 |
| `components` | integers 2 through 5 |
| `color_policy` | `distinct`, `repeated` |
| `layout` | `separated`, `tied`, `crossing` |

All combinations of these advertised values were checked at one seed/index
per tuple across `None`, `easy`, `medium`, `hard` (6,048 cases, Python oracle).
Explicit dimensions/counts take precedence over difficulty defaults. `None`
means omit that override. Booleans, floats and numeric strings are not integer
overrides. Unknown or retired axes raise errors rather than silently doing
nothing. Background and palette range are fixed; colors themselves are sampled.

Without overrides, four consecutive examples at one seed cover all four
profiles and refute the four declared rivals. Fewer demonstrations or forced
semantic axes do not inherit that guarantee. No assertion of uniqueness among
all possible rules or of downstream model improvement is made.
