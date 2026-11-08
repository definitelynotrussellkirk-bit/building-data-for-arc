# Workspace and source-bound shortcut probe

The selected implementation is `../generator.py`; workspace modules are not
selected as production generators. `shortcut_probe.py` is a reusable,
task-specific audit tool for version-to-version comparisons.

## Run from an extracted review packet

The wrapper changes the working directory to `repo` and activates the supplied
Racket runtime. The probe stages a complete relocated runtime through
`arcpuzzles.runtime.prepare_runtime`; importing only `shared/runtime` is not enough.

```bash
python3 setup_racket.py
python3 run_with_racket.py python3 generators/6d19cd1698b1/workspace/shortcut_probe.py \
  --out ../checks/shortcut-current.json \
  --cases-out ../checks/shortcut-current.jsonl --require-refuted
```

Compare the frozen assignment baseline without changing selected sources:

```bash
python3 run_with_racket.py python3 generators/6d19cd1698b1/workspace/shortcut_probe.py \
  --generator ../.review/baseline/repo/generators/6d19cd1698b1/generator.py \
  --out ../checks/shortcut-baseline.json \
  --cases-out ../checks/shortcut-baseline.jsonl
```

In a normal source checkout with dependencies and Racket already available:

```bash
python3 generators/6d19cd1698b1/workspace/shortcut_probe.py \
  --repo . --out /tmp/shortcut-current.json --require-refuted
```

`--seeds` defaults to 128, with sample index zero and None/easy/medium/hard
bands. A separate sweep uses each declared scene profile at 3x7 and 10x14,
eight seeds per band. Profiles are inferred from inputs; no provenance label
is used to establish a witness. `--exhaustive-width 0` disables the default
3^7 local-row parity stress test; widths above eight are rejected.

The JSON includes generator, canonical-row, normalized-rule, tool and optional
case-file hashes; all draw parameters; exact first rival witnesses; canonical
label checks; mutation/replay checks; and before/after-comparable counts.
Cases JSONL contains actual Racket outputs, not Python-assigned labels.

Exit zero requires all validity, canonical and parity checks to pass.
`--require-refuted` additionally requires both structural rivals to be refuted
by default draws. It is expected to fail on version 2.0.0, so omit it for that
baseline measurement. An unrefuted rival is not silently marked a pass.
This suite is specific to this task; adapt the rival definitions, canonical
parsing, profiles and boundary plan deliberately before copying it elsewhere.
