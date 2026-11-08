# Task-local diagnostic tools

The selected implementation is `../generator.py`; none of these scripts replaces
the Racket authority or changes another task. Run the following from `repo` with
`PYTHONPATH=src` and a working `RACKET_PATH`/PATH, or prefix each command with the
packet-root wrapper `python3 run_with_racket.py`.

## Translation distribution and parity

```sh
python3 generators/2376352117fc/workspace/probe_translation.py --root . --out ../checks/new-probe --seeds 128 --racket --expect-improved
```

The output directory must not already exist. The cohort is seeds `[0, seeds)`,
indices 0–7, and easy/medium/hard. Outputs are a hash-bound `report.json`, per-draw
`samples.jsonl`, and full `witnesses.json` counterexamples. Every requested Racket
comparison is checked, not only the first case. Reports distinguish draws,
unique inputs/outputs, shapes up to translation and dihedral symmetry, canonical
acceptance, semantic profiles, and shortcut disagreements. A source-layout call
stages the supported portable runtime automatically. A pre-staged runtime root
is also supported. `--generator /path/to/old/generator.py` permits a baseline
comparison; omit `--expect-improved` for a known-old baseline. Never use the
optional Python-only mode to claim authoritative label parity.

## Read-only audits of the two drawn targets

```sh
python3 generators/2376352117fc/workspace/audit_assigned_targets.py --root . --out ../checks/new-audits --seeds 128
```

Targets are fixed in the script to this assignment's two audit draws. Per target:
384 default draws at the default seed bound, canonical parity, a rival, one
forced-axis cohort, and an exact Racket-evaluated counterexample. The script
normalizes both row-string grids and singleton/list test representations. Findings
are not automatic repairs or admission decisions. The longest-wire rival fits
canonical examples; the one-sided mirror rival does not, so those findings have
different evidential status.

## Relocation and optional read denial

```sh
python3 generators/2376352117fc/workspace/verify_relocation.py --root . --racket-root ../.review/racket-runtime/racket --out ../checks/new-isolation
# On a host without Landlock, a weaker portability-only check is explicit:
python3 generators/2376352117fc/workspace/verify_relocation.py --root . --racket-root ../.review/racket-runtime/racket --out ../checks/new-relocation --guard none
```

This copies a runtime into a fresh `/tmp` directory and runs isolated Python
(`-I`) with a copied Racket runtime. It records the actual runtime path, source
hashes, exact argv, logs, and a 192-draw plus 4-canonical parity probe. The default
Landlock mode fails closed if enforcement is unavailable. `--guard none` makes
**no claim that original-source reads are denied**. Only receipts/evidence are
retained, not the installed runtime or duplicate repository. This review's kernel
returned ENOSYS for Landlock; the separately labeled unguarded relocation check
is weaker evidence, not a substitute security proof.

## Regression tests

```sh
python3 -m pytest -q generators/2376352117fc/tests
```

The local suite covers semantic boundaries, strict/observable overrides, endpoint
cross-products, reproducibility, malformed inputs, cyclic lesson windows, the
actual intermediate failure, and canonical-format normalization in the audit tool.
The repository's default pytest collection does not replace this explicit run.
