# Reusable lesson probe

Run from the extracted packet root, after finalizing `generator.py`:

```bash
python3 run_with_racket.py python3 generators/59c2f0a5d4a9/workspace/lesson_probe.py --out ../checks/lesson-final --lessons 100 --seed 20261003
```

The wrapper sets the Racket executable and changes the working directory to
`repo`. The output directory must be new. For an explicitly preliminary small
diagnostic, add `--phase preliminary --lessons 3` and choose a separate output
directory. `--timeout` defaults to 900 seconds **per public API call**.

The tool dynamically imports the selected task generator and enumerates the
actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` dictionaries. Every declared
shortcut must fit every usable canonical pair, including labeled canonical
queries. All declared rivals are measured; a shortcut omitted from the lesson
dictionary is still included. Conflicting definitions under one name fail
visibly.

For each of easy, medium, and hard, the default run materializes 100 actual
`Catalog.generate` lessons with three demos and two queries. The count is split
34/33/33 across `sample_index` starts 0/1/2. Seeds advance through a recorded,
nonoverlapping range. The public runner increments the episode seed and scans
consecutive indices until it accepts five valid, distinct pairs. The probe
retains the actual accepted indices and every rejection, and independently
regenerates every accepted input to verify the seed/index interpretation.

It also checks all three overlapping five-draw windows at a fresh seed in each
band. These use indices 0..6 and canonical Racket outputs from `Catalog.apply`;
no call supplies more than 64 inputs. The three windows per band are reported
separately from the 100 actual-runner lessons and are not presented as 15 unique
inputs. No private reference-runner helper is imported or called.

Each rival/lesson is classified as demo-refuted, surviving with both query
outputs agreeing, surviving with at least one query output disagreeing, or
execution error. A rival exception is never counted as successful refutation.
The selected generator's `lesson_identifiable` hook, if present, is checked for
each of the two queries separately. Default controls are measured; explicit
overrides can supersede the three-state teaching schedule and require their own
scope and evidence.

`summary.json` and `REPORT.md` give source hashes, exact seed/index ranges,
denominators, unique-input counts, categories, and failures. `pairs.jsonl`
deduplicates full inputs/outputs; `lessons.jsonl` contains references and every
rival result. `programs.jsonl` stores each executed program once, so the complete
public episode can be reconstructed and checked against its retained payload
hash. `rival_evidence.jsonl` retains full rival outputs for decisive
examples and all harmful survivors/errors. `canonical.json` contains all
canonical comparisons; `apply_receipts.jsonl` retains complete public Racket
receipts. All failures are retained in `failures.jsonl`, when present. Earlier
output directories are never overwritten. Small `generator_source.py` and
`probe_source.py` snapshots retain the exact implementation measured by each
run; the source hashes still refer to their authoritative paths in the repo.

Source bytes are checked before public API calls and at completion. A source
change invalidates the run. Final mode requires at least 100 actual lessons per
band and all three direct cyclic starts; smaller runs are explicitly preliminary.
A passing census is a finite measurement against the declared rivals, not a
claim of universal induction or a change to training approval.
