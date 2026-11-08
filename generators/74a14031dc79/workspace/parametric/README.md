# Proposed occupancy-rule parameter prototype

Status: **proposed and unapproved**. This workspace does not alter the selected
production generator's canonical `OR` rule, `RULE_HASH`, sampling distribution,
or ordinary generation path.

The episode-level parameter is `occupancy_rule` with bounded values:

- `or` — canonical/default: output blue when either aligned panel cell is occupied;
- `xor` — output blue when exactly one aligned panel cell is occupied;
- `and` — output blue only when both aligned panel cells are occupied.

The object roles, `3 + separator + 3` geometry, aligned-cell comparison, and blue
output code remain invariant. The parameter is selected once from the episode
seed and reused for every demonstration and query in that episode.

## Episode sizes and support

Demonstration and query counts are independent:

- default demonstrations: `3`;
- default queries: `4`;
- supported range: `1..16` for each count.

The sampler deterministically rejects duplicate inputs, so the default episode
contains seven distinct grids. Every retained input comes from the selected
production generator and contains the complete `00`, `10`, `01`, `11` occupancy
truth table. Thus each demonstration individually distinguishes the three
declared settings, while four distinct query grids test the same inferred rule.
If the bounded sampler cannot obtain the requested number of unique lawful
inputs, it fails rather than cloning pairs.

All labels are computed by executing the exact materialized Racket program
through `RacketBridge`; there is no Python answer implementation. The canonical
`or` source is checked byte-for-byte against the pinned authority.

## Public export contract

Public challenge bytes contain only demonstration inputs/outputs and query
inputs. They omit seeds, hidden settings, Racket source, rule hashes, private
metadata, and query answers.

Each public filename is the SHA-256 returned by
`reviewer_support.public_challenge_id`, computed from the exact bytes returned by
`reviewer_support.public_challenge_bytes`. Batch output is sorted by that ID.
Duplicate visible challenges are rejected rather than receiving seed- or
order-derived suffixes. Therefore changing seed order or private fields cannot
rename an unchanged public challenge.

## Reproduction

From the outer extracted packet directory, run:

```sh
python3 review.py run python3 \
  generators/74a14031dc79/workspace/parametric/prototype.py \
  --seeds 1 0 5 \
  --demos 3 \
  --queries 4 \
  --out ../checks/parametric/occupancy-rule-v2
```

Seeds `1`, `0`, and `5` exercise `or`, `xor`, and `and`, respectively. The output
directory must not already exist. Focused tests:

```sh
python3 review.py run python3 -m pytest -q \
  generators/74a14031dc79/tests/test_parametric_occupancy_rule.py
```

The evidence writer produces private source-bound episodes, exact public
challenge bytes, canonical replay results, a distinguishing witness, source/file
hashes, and a manifest. The retained finite check covers only the three declared
settings and supplied seeds; it does not prove unique induction against every
conceivable rule, approve these variants for training, or change the production
generator.

## Current replay and separate public-focus proposal

`verify_evidence(path)` replays the current writer's retained episodes through
Racket, checks deterministic episode bytes, counts and unique inputs, and verifies
visible public IDs and exact masking. This ports the useful verifier from
`review-2a5829cdd071ba0c` while preserving the current independent `1..16` count
bounds and sorted writer. The earlier `review-9f9da496aea2f906` count/ID changes
are already present in the selected prototype.

The separate [16de56c4 public-focus proposal](../public_focus_16de56c4/README.md)
has Python and proposed Racket implementations with focused demonstration/support
checks. Its two actual public query predictions remain unverified. It has no
verified lineage to this occupancy family, approval or training admission.
