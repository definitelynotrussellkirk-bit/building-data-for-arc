# Reusable review tools

All tools are local diagnostics; they never label exported training examples or
change the selected Racket authority. Commands below run from the extracted
packet root; `run_with_racket.py` enters `repo`.

## Source-hashed before/after quality census

```bash
python3 run_with_racket.py python3 generators/f9dd4cf0f344/workspace/quality_probe.py --count 256 --racket --out ../checks/probe-final-v3-racket.json
```

Supports `--generator ../.review/baseline/repo/generators/f9dd4cf0f344/generator.py`
for an immutable baseline comparison. Each band uses seeds 0..255 and
sample_index=seed. Reports per-band input uniqueness, identities, independent
wrong-rule agreement, concrete first counterexamples, source hashes, and actual
Racket/Python parity. Exit 1 means a generation or parity failure. A clean
census is not a model-training result or universal correctness proof.

## Canonical-counterexample retention gate (findings-only audit adapters)

```bash
python3 run_with_racket.py python3 generators/f9dd4cf0f344/workspace/canonical_rival_probe.py --count 256 --gate --out ../checks/canonical-retention-gate.json
```

Adapters currently cover assigned audit targets `8b595f6acd93` and
`c36d1678a484`. The tool checks all sampled and canonical labels with Racket,
then reports any canonical-refuted rival that survives every sampled draw in a
band. Exit 2 means coverage gaps; exit 1 is measurement failure; exit 0 is
completion without gaps. Without `--gate`, a completed measurement exits 0 even
when its report says FAIL. The current audited row generator intentionally
makes `--gate` exit 2; the audit targets were not repaired in this assignment.

To add another adapter, implement independently tested `reference` and `predict`
functions and add the task to RIVALS. Canonical refutation establishes that a
candidate is actually wrong before missing generated counterexamples can veto.
This finite-rival, finite-census prototype is not a complete semantic checker.

## Relocated-runtime verification

```bash
python3 run_with_racket.py python3 generators/f9dd4cf0f344/workspace/portable_probe.py --out ../checks/portable-final.json
```

Copies the supported execution layout, moves it to a different directory, drops
PYTHONPATH/PYTHONHOME, and checks 32 seeds in each band against Racket. Reports
actual temporary runtime and import origins; temporary trees are removed, not
returned. It does not depend on an editable installation of another checkout.

## Task-local regression tests

```bash
python3 run_with_racket.py python3 -m pytest -q generators/f9dd4cf0f344/tests
```

The repository's bare pytest command does NOT discover these task-local tests.
`history/generator-v1.py` and `generator-v2.py` are failed/intermediate drafts,
not alternative selected generators. Never select them for training.

## Query-sensitive lesson gate (public data only)

After applying this delta to the packet, run from packet root:

```bash
python3 repo/generators/f9dd4cf0f344/workspace/lesson_ambiguity_gate.py --challenge solve/challenge.json --candidates solve/candidates.py --out checks/lesson-ambiguity-final.json
```

A trusted local adapter exports CANDIDATES: dict[str, callable]. Each callable
is tested on copied visible inputs. Visible-consistent candidates are compared
on query inputs; no reference query labels are accepted or read. Exit 2 denotes
AMBIGUOUS, exit 1 measurement error/incompleteness, exit 0 no disagreement within
the reviewed finite registry. The supplied episode returns 2 intentionally.
Do not treat this tool as a sandbox for untrusted or nonterminating Python.
The adapter imports the original episode's three public-only candidate
functions; solve attempts and private score policy remain untouched.
