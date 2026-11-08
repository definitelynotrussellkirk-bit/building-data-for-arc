# Reusable review tools

The selected implementation is `../generator.py`. Workspace tools are never
automatically selected as generators. Run the examples below from the extracted
review packet root. The Racket wrapper changes its child working directory to
`repo`; command paths inside the wrapper therefore begin at the repository.

## probe_distribution.py — actual Racket lessons and rivals

Imports the actual selected generator and its actual
`CANONICAL_SHORTCUTS` / `LESSON_COMPETITORS` declarations. It verifies source
and rule identity, checks all stored canonical pairs, calls public
`Catalog.generate` for authoritative labels, and compares them with an
independent checking oracle. It records unique draws, unique inputs, overlapping
lesson windows, witness frequencies, sample indices and first counterexamples.

```bash
python3 run_with_racket.py python3 \
  generators/b985d561c63b/workspace/probe_distribution.py \
  --library . --out ../checks/probe_new \
  --lessons 100 --seed 140000 --short-lesson-probe
```

Use a new output directory. The default plan covers three difficulty bands,
starts 0/1/2, three demonstrations and two queries. One hundred seeds per band
give 300 distinct (band,seed) base lessons plus 600 overlapping windows, rather than
900 independent seeds. Output includes summary.json, instances.jsonl,
lessons.jsonl and complete first counterexamples.

The retained final run is under checks/final_probe_final. A finite-rival pass
does not establish universal induction or measured model learning quality.
The optional short-lesson probe deliberately demonstrates a public one-demo
admission gap; it is a diagnostic, not a natural failed solve.

## episode_gate.py — check the actual labeled episode

Consumes an episode JSON with labeled train/test pairs and source provenance.
It binds the selected generator bytes, canonical source/RULE_HASH and retained
sample indices, then evaluates actual declared rivals against every demo and
query. It permits answer-equivalent survivors.

```bash
python3 run_with_racket.py python3 \
  generators/b985d561c63b/workspace/episode_gate.py \
  --generator generators/b985d561c63b/generator.py \
  --episode ../checks/final_probe_final/short_lesson.json \
  --out ../checks/episode_gate/short_replay.json
```

Use a new output receipt. Expected exit for this retained short episode is 1.
The retained full episode at checks/episode_gate/full_lesson.json should return 0.

| Exit | Meaning |
|---|---|
| 0 | No surviving declared rival disagrees on any emitted query |
| 1 | A rival fits all demos and disagrees with a query label; receipt names it |
| 2 | Malformed/unlabeled episode, invalid rival declaration, or source mismatch |

This tool reuses supplied labels and provenance; it does not execute Racket
again or certify the labels' origin. It does not grant generator approval.
Integration into the shared generation/export path is proposed in feedback F1,
outside this allowed task-local delta.

## replay_return.py — verify a return against its original packet

Standard-library CLI needing Python 3.12+, Git and the packet's test dependencies.
It verifies the original ZIP inventory/hashes, creates a new extraction, invokes
the original return validator, uses Git to check allowed patch paths, runs
git apply --check and git apply, binds generator and solve-source hashes, sets
up offline Racket and runs all selected-task tests through the fresh wrapper.

```bash
python3 repo/generators/b985d561c63b/workspace/replay_return.py \
  --original /absolute/path/to/original_packet.zip \
  --return /absolute/path/to/candidate_return.zip \
  --out /absolute/path/to/new_fresh_packet \
  --report checks/fresh_replay_new.json \
  --expected-generator-sha256 c8acb6b749fa8817826507cfa27043773d462b7791fd50f5ffa7716d7107fc1d
```

Output directory and report must not exist, and their parent directories must
exist without symlinks. The tool retains exact commands, effective working
directories, statuses, source and patch hashes, and focused test counts.
It does not draw a new assignment, run the submitted solver or read private
query labels. Failure leaves an honest receipt and the partial extraction.

## Focused tests

The repository's ordinary test discovery does not include task-local tests.
Invoke them explicitly:

```bash
python3 run_with_racket.py python3 -m pytest \
  generators/b985d561c63b/tests -q
```

The final suite has 279 tests: 248 generator-contract cases, 8 smoke/tight-layout
regressions, 16 replay-helper checks, and 7 episode-gate checks.
Review evidence compression/restoration is explained by the return's checks/README.md.
