# Row-wave authoring tools

The selected implementation is `../generator.py`. This directory contains authoring probes, not an alternate generator or a Python source of training labels. The Racket authority remains the selected canonical rule.

## Inspect the declared rivals

From the outer extracted packet folder, after `python3 review.py setup`:

```bash
python3 review.py run python3 generators/8a3fe170ed27/workspace/probe_rivals.py --out ../checks/new-rival-probe
```

Use a fresh output directory. The probe resolves the repository or staged runtime with `reviewer_support.find_root` and `load_selected_generator`, inventories the actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_RIVALS` declarations, deduplicates callable aliases, and checks purity and determinism. It retrieves all usable canonical pairs through the public helper and labels its small input batch through `Catalog.apply(reference="canonical", check_generator_domain=True)`. It saves exact inputs, the public Racket receipt, source/rule hashes, every rival's canonical-fit result, and its first generated counterexample. A successful probe checks the declared finite candidates; it does not establish unique induction or approve training admission.

This probe can be adapted to another selected task by changing its task constant and task-specific input recipes. It does not depend on private per-puzzle import aliases or a fixed directory depth. Do not run authoring probes in either visible-only solve phase: canonical helpers expose answers.

## Run the focused regression suite portably

With pytest, NumPy and Pillow available in the interpreter used by the wrapper:

```bash
python3 review.py run python3 -m arcpuzzles check 8a3fe170ed27 --stage task_tests --phase after --timeout 600 --out ../checks/new-task-tests
```

The public stage snapshots the selected source, task tests, canonical helpers and any frozen fixtures into its own runtime. Missing or skipped tests are not a pass. Inspect the reported source hash and counts.

## Check complete lessons

Default lessons use **four demonstrations and one query** from consecutive sample indices. The four-position schedule is structured interior, irregular left, irregular interior, irregular right. Sparse tails in the irregular profiles have phase offsets 1, 2 and 3 modulo four. Every five-pair window contains all three; after any single query holdout, demonstrations still contain two distinct offsets. This refutes the declared constant-offset anchor shortcuts while preserving at least one of the two edge-clipping examples.

```bash
python3 review.py run python3 -m arcpuzzles lesson-census 8a3fe170ed27 --enumerate-schedule-period --schedule-seed 0 --rotation-policy require --out ../checks/new-schedule-census.json
python3 review.py run python3 -m arcpuzzles check 8a3fe170ed27 --battery --compact-results --require-rotations-identifiable --schedule-census ../checks/new-schedule-census.json --schedule-seed 0 --phase after --timeout 4000 --out ../checks/new-after
python3 review.py run python3 -m arcpuzzles lesson-census 8a3fe170ed27 --per-band 100 --rotate-query --rotation-policy require --timeout 1800 --out ../checks/new-lesson-census.json
```

The schedule census exhausts four start residues at one fixed seed across the three bands. The larger census samples production lessons; overlapping windows are not independent inputs. Report the unique-input denominator separately. Explicit override draws are research cases: small or solid motifs can be lawful without carrying the ordinary curriculum's teaching guarantees.

## Evidence in this return

`WORK/checks/` retains baseline and intermediate failures, final source-bound reports, both findings-only audits, and replay checks. Large reports may be stored losslessly as individual gzip files; `checks/compressed/MANIFEST.json` maps original paths, sizes and SHA-256 hashes, and `checks/compressed/RESTORE.md` gives restoration commands. The final verification records distinguish the unchanged Racket authority from synchronization of the selected archival target string.

## Prototype a rule parameter without changing production

`parametric/` contains a runnable proposed extension that varies one
`wave_orientation` setting per episode while preserving the last-active-row,
distance-modulo-four, whole-row-translation reasoning pattern. The canonical
`left_first` setting remains the default; `right_first` is a mirrored proposal.
Its four demonstrations are required to distinguish the opposite setting. See
`parametric/README.md` for the exact source-bound Racket execution command,
public examples, hashes, and limits. Nothing under `parametric/` is imported by
`generator.py` or the selected canonical execution path.
