# Parametric prototype: `86af5978a32a`

## Purpose

This task-local adapter preserves the selected canonical layout×mask expansion
rule exactly and adds one episode-fixed finish parameter:

- `stamp_only` — exact canonical Racket program bytes.
- `highlight_largest_component` — perform the canonical expansion, collapse the
  stamped output to binary occupancy, select its unique largest 4-connected
  component, and recolor that component to color 9.

The second setting is intentionally sequential. The component chosen in the
final step exists only after the input-derived layout and mask have been
expanded; differently colored neighboring stamps may merge in binary occupancy.
The retained counterfactual instead computes color-sensitive components and
selects a different final component.

## Replay commands

Run these commands from the packet's outer directory, the directory containing
`review.py`:

```bash
python3 review.py task-tests 86af5978a32a --phase after \
  --out ../checks/86af5978a32a-tests-replay

python3 review.py run python3 \
  generators/86af5978a32a/workspace/parametric/probe.py \
  --seed 0 --seed 17 --seed 97 --demos 6 --queries 4 \
  --out generators/86af5978a32a/workspace/parametric/evidence/current/authoring-probe.json

python3 review.py run python3 -m arcpuzzles parametric qualify 86af5978a32a \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/86af5978a32a/qualification-replay --summary

python3 review.py run python3 -m arcpuzzles.review_witness check \
  --qualification ../checks/86af5978a32a/qualification/qualification.json \
  --witness ../checks/86af5978a32a/causal/witness.json \
  --out ../checks/86af5978a32a/causal/recheck.json
```

The checked native qualification retained by this review is at
`checks/86af5978a32a/qualification/`; the protected-Racket causal witness is at
`checks/86af5978a32a/causal/witness.json`.

## Contracts and limits

- Demonstrations: 2–6.
- Queries: 1–4; the production target is four distinct queries revealed one at
  a time.
- Inputs are sampled independently of the private setting, so matched requests
  produce matched inputs across settings.
- Maximum lawful output under the retained production grammar is 25×25
  (`k = 5`, output side `k²`); a literal 30×30 case is not source-lawful.
- The authoring audit attacks a finite rival bank only. Passing it is not a
  proof of uniqueness among all possible rules.
- `ready` or `qualified` is reviewer evidence, not owner acceptance. These
  variant bytes are not training-admitted.

## Source identities

- Production generator SHA-256:
  `ee84cd19b1f4ccb64bb6a089b497acacae3c195c16fd3fbe100c83c4b3238a0e`
- Canonical/default Racket SHA-256:
  `a6914eb76bfb0d5fbd5a1ed0dc1933807388909461277ac7c0d7b2ac830ca2b5`
- Alternative Racket SHA-256:
  `6ad1968277250470da4aca819dd4e5ddd31e35a1b5b9db8dc37cf3a7cac48c02`
- Counterfactual Racket SHA-256:
  `0418929b0057dca67eb33faab946b5c29a1ef860c152abab55f9a42fe1234e2a`
