# Proposed occupancy-rule parameter prototype

Status: **proposed and unapproved**. This workspace does not alter the selected
production generator's canonical `OR` rule, `RULE_HASH`, approval, or ordinary
sampling path.

The episode-level parameter is `occupancy_rule` with bounded values:

- `or` — canonical/default: output blue when either aligned panel cell is occupied;
- `xor` — output blue when exactly one aligned panel cell is occupied;
- `and` — output blue only when both aligned panel cells are occupied.

The object roles, `3 + separator + 3` geometry, aligned-cell comparison, and
blue output code remain invariant. The parameter is selected once from the
episode seed and reused for every demonstration and query. Demonstration and
query counts are requested independently with `--demos` and `--queries`; each
must be a literal integer in `1..12`. The writer returns exactly the requested
number of distinct inputs or fails rather than cloning examples or silently
returning fewer.

Every input is drawn from the selected production generator and contains the
complete `00`, `10`, `01`, `11` occupancy truth table. Therefore each retained
demonstration distinguishes `or`, `xor`, and `and`; the demonstrations alone
identify the selected finite-rule setting before any query answer is considered.
All labels are computed by executing the exact materialized Racket program
through one `RacketBridge`; there is no Python answer implementation.

Public challenge bytes contain only demonstration inputs/outputs and query
inputs. Their filenames are `challenge-<sha256>.json`, where the digest is of
the exact visible bytes written by `reviewer_support.public_challenge_bytes`.
Seeds, settings, Racket source, rule hashes, and query outputs remain private,
and changing those private fields does not change the public ID.

From the outer extracted packet directory, generate the retained three-setting,
four-query evidence:

```sh
python3 review.py run python3 \
  generators/74a14031dc79/workspace/parametric/prototype.py \
  --seeds 1 0 5 \
  --demos 3 \
  --queries 4 \
  --out ../checks/parametric/occupancy-rule-v2
```

The three seeds exercise `or`, `xor`, and `and`, respectively. The output
directory must not already exist. Focused tests:

```sh
python3 review.py run python3 -m pytest -q \
  generators/74a14031dc79/tests/test_parametric_occupancy_rule.py
```

The evidence writer produces private source-bound episodes, exact rule
snapshots, canonical replay results, a distinguishing witness, content-addressed
public challenges, source/file hashes, and a manifest. The retained run contains
three demonstrations and four distinct queries for each setting. Its finite
rival check covers only the three declared settings and supplied seeds; it does
not prove unique induction against every conceivable rule or approve these
variants for production or training.
