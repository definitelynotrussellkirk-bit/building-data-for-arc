# Proposed occupancy-rule parameter prototype — v2

Status: **proposed and unapproved**. This workspace does not alter the selected
production generator, its canonical `OR` behavior, or rule hash `582367af483f`.

The bounded episode parameter is `occupancy_rule ∈ {or, xor, and}`:

- `or` — canonical/default: output blue when either aligned panel cell is occupied;
- `xor` — output blue when exactly one aligned panel cell is occupied;
- `and` — output blue only when both aligned panel cells are occupied.

All settings preserve the original `3 + separator + 3` geometry, aligned-cell
comparison, object roles, and blue output code. The setting is selected once from
the episode seed and held fixed across independently configurable demonstrations
and queries. Every generated input contains all four relations `00`, `10`, `01`,
and `11`, so each demonstration refutes both unselected settings.

## v2 correction

The earlier external follow-up was explicitly pending because it hard-coded
three demonstrations/one query and named public files `episode-NNN.json`, which
leaked private batch order. v2 repairs both boundaries:

- `--demo-count` and `--query-count` are independent positive literal integers;
- the default is **3 demonstrations and 4 distinct queries**;
- at most 16 total pairs are supported per episode, with bounded duplicate retries;
- every retained label, including all query labels, is executed by exact Racket;
- public files are named `challenge-<sha256>.json`, where the digest is computed
  from the exact visible challenge bytes only;
- batch rows are sorted by that public ID before private `episode-NNN.json`
  ordinals are assigned, so input seed order cannot leak through output order;
- private seed, setting, Racket source, and query answers cannot affect the public
  identifier; changing a visible query input does;
- the verifier replays private episodes, all Racket labels, pair counts, distinct
  inputs, public bytes, and content-derived identifiers.

## Reproduce retained evidence

From the outer extracted packet directory:

```sh
python3 review.py run python3 \
  generators/74a14031dc79/workspace/parametric/prototype.py \
  --seeds 1 0 5 \
  --demo-count 3 \
  --query-count 4 \
  --out ../checks/parametric/occupancy-rule-v2
```

Seeds `1`, `0`, and `5` exercise `or`, `xor`, and `and`. The output directory must
not already exist. The retained run contains 3 episodes, 9 demonstrations, 12
distinct queries, 21 Racket-replayed labels, zero surviving declared parameter
rivals, and three opaque public IDs.

Focused tests:

```sh
python3 review.py run python3 -m pytest -q \
  generators/74a14031dc79/tests/test_parametric_occupancy_rule.py
```

The adversarial record at `checks/parametric/adversarial-v2/result.json` retains
two changed-surface attacks: the 16-pair support boundary (12 demos + 4 queries)
and rejection of 17 pairs, plus public/private identifier independence and
verifier rejection of tampered public bytes.

## Limits

This is finite, source-bound evidence for the supplied seeds and the three declared
Boolean settings. It does not prove unique induction against every possible rule,
approve variants for training, or create a production parametric API. The OR
setting is byte-identical to the pinned canonical Racket source; XOR and AND remain
separate proposed programs.
