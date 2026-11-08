# Parametric bar-length prototype

This directory is a **separate authoring prototype**, not a change to the selected production rule. The episode-level parameter is `bar_length ∈ {1, 3}`. It is chosen once and held fixed across every demonstration and query in an episode.

- `bar_length=3` is the canonical/default setting. Its Racket source is byte-identical to the canonical ledger program.
- `bar_length=1` keeps the same object analysis, target choice, and three non-target tip erasures, but paints only the center cell of the outside bar.
- Inputs come from the selected generator family and do not depend on the parameter.
- Every output and rival prediction is produced by `RacketBridge`; there is no Python label fallback.
- Public challenge JSON contains demonstration outputs and query inputs only. The chosen parameter, rule source, rival outputs, and query answers remain in private evidence.

From the outer packet directory, produce retained evidence and public examples with:

```bash
python3 review.py run python3 generators/474634a9f7b7/workspace/parametric/prototype.py \
  verify --seed 0 --seed 17 \
  --out ../checks/parametric/bar-length-v1 \
  --write-public generators/474634a9f7b7/workspace/parametric/examples
```

The output directory must not already exist. The prototype checks exact canonical authority, executes all canonical labels, runs both parameter settings on a lawful separating witness, materializes complete episodes, and confirms the alternative setting is refuted by the demonstrations.
