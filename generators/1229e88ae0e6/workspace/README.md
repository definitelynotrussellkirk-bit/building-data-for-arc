# Workspace

The selected implementation remains `../generator.py`; these tools do not replace
the Racket reference or change an approval label. They require Python 3.12+ and
the supplied repository helpers (including NumPy).

From the packet directory, run the paired-relation support gate:

```bash
python3 -B repo/generators/1229e88ae0e6/workspace/review_probe.py \
  --out checks/support_replay.json --require-support
```

The gate compares canonical movement classes with a 200-input census per band
and the four-demo export's fixed first-query index over seeds 0..31. It also
checks mirrors, strict acceptance, and lesson windows. `--generator PATH` loads
a frozen baseline source; a failing gate exits nonzero. `--seed` and `--count`
control the ordinary census. `--library PATH` selects another complete checkout.

Run the ordinary-episode shortcut audit (including generic rivals that the
generator may have forgotten to declare):

```bash
python3 -B repo/generators/1229e88ae0e6/workspace/shortcut_audit.py \
  --out checks/shortcut_audit.json --require-none
```

It evaluates indices 0..3 as demonstrations and index 4 as the query over 512
seeds per band by default. The JSON records demonstration survivors, harmful
query disagreements, per-band counts, and the first reproducible seed. Use
`--generator PATH` to compare a frozen candidate or baseline and `--seed-count`
to change the census. In addition to declared semantic rivals, it probes color
sorting, exact-hole packing, motif transforms, palette reversal, and source-copy
shortcuts so an omitted rival can still be discovered.

Run the finite-domain and multi-seed stress probe:

```bash
python3 -B repo/generators/1229e88ae0e6/workspace/stress_review.py \
  --out checks/stress_replay.json
```

This covers 142 supports, all their noncentered canonical-canvas placements under
two deterministic coloring schemes, all supported overrides across slots and
selected seeds, sliding lessons, declared rival killers, and metamorphic properties.
All generated outputs in these tools are explicitly **diagnostic Python outputs**.
They are not independent Racket parity evidence or training data.

For official execution, use the unchanged battery from inside `repo/`:

```bash
PYTHONPATH=src python3 -B -m arcpuzzles check 1229e88ae0e6 \
  --battery --timeout 4000 --out ../checks/racket_replay
```

The original task test file is included by the runtime manifest. New workspace
tools are run from this library layout, not automatically copied to the legacy
runtime. Use at least four demonstrations for this generator; the public
`generate` API's generic default of three does not satisfy its lesson contract.
