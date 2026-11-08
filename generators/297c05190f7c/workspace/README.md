# Review workspace

The selected implementation is `../generator.py`; files here are review tools or
retained evidence sources and are never selected automatically.

- `baseline_generator_2.0.0.py` is the exact source before the first spatial and
  extent repair.
- `baseline_generator_2.1.0.py` is the exact source before the topology and
  density repair.
- `baseline_generator_2.2.0.py` is the exact source before the fill-depth,
  scale, aspect, and same-color-grouping repair.
- `distribution_probe.py` independently reconstructs 4-connected components,
  the intended output, and the round-one corner/extent rivals.
- `shortcut_miner.py` independently reconstructs components and evaluates 18
  canonical-fitting rivals from all three rounds. It does not call the selected
  generator's private analyzer, rule mirror, rivals, or witnesses. Reports
  include source identity, seed range, denominator, unique-input count,
  property support, disagreement counts, and first exact counterexamples.
- `run_focused_tests.sh` builds a disposable task runtime and runs the task-local
  regression file without borrowing an installed repository environment.

From the packet root:

```bash
bash repo/generators/297c05190f7c/workspace/run_focused_tests.sh

python3 repo/generators/297c05190f7c/workspace/distribution_probe.py \
  --generator repo/generators/297c05190f7c/generator.py \
  --samples-per-profile 100 \
  --out checks/distribution-round3-after.json

python3 repo/generators/297c05190f7c/workspace/shortcut_miner.py \
  --generator repo/generators/297c05190f7c/workspace/baseline_generator_2.2.0.py \
  --samples-per-profile 100 \
  --out checks/shortcut-miner-round3-before.json

python3 repo/generators/297c05190f7c/workspace/shortcut_miner.py \
  --generator repo/generators/297c05190f7c/generator.py \
  --samples-per-profile 100 \
  --out checks/shortcut-miner-round3-after.json
```

Both probes default to seeds `[0,100)`, all three difficulties and profiles,
and forced dimensions 8x9. Under those controls there are 900 successful
attempts. Reports distinguish attempt count from unique-input count and pin the
loaded source by SHA-256.
