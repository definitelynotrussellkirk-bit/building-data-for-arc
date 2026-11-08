# Reusable probes and next-agent handoff

Task: `f2dbde875127`; assignment: `review-5994a478cf362114`.
Final source SHA256:
`b3adc8e5389ad39d70f4b5dd9828f3352f9de1195c9d67f29139c7d5c3e10b92`.
Run from the extracted packet root after applying the cumulative patch.

## Fast source-only regression

```bash
python -m pytest -q repo/generators/f2dbde875127/tests
python3 -E -s repo/generators/f2dbde875127/workspace/distribution_contract_probe.py \
  --count 256 --out checks/distribution-contract-replay.json
```

`distribution_contract_probe.py` reads no labels and bootstraps the packet-local
`repo/shared/runtime` without relying on caller `PYTHONPATH`. It binds itself to
the current generator and checks three finite contracts: no exact same-seed replay across
easy/medium/hard, every ordinary framed object starts off-center, and every
four-sample first-frame-key window covers 2/3/4/5. Nonzero exit means at least
one measured contract failed. It is not a general diversity proof.

## Inherited battery

```bash
python setup_racket.py
python run_with_racket.py python -m arcpuzzles check f2dbde875127 \
  --battery --timeout 4000 --phase after --out ../checks/maintainer-battery
```

When the caller kills a monolithic command, run the documented twelve stages
individually with `--stage` and retain every `result.json`. This round's
`checks/round2-battery-final-summary.json` aggregates twelve official isolated
receipts; each per-stage native summary naturally marks the other eleven stages
pending.

## Actual-episode public-only gate

```bash
python run_with_racket.py python \
  generators/f2dbde875127/workspace/episode_identifiability_probe.py \
  --count 4 --start-seed 0 --out ../checks/episode-batch0.json
```

Repeat with disjoint start seeds when command windows are short. The probe asks
the real runtime for Racket-labeled episodes, deep-copies complete demonstration
pairs, removes every query output, and only then calls `lesson_key_gate.py`.
It records sample indices, candidate rejections, source/rule hashes, observed
key frames, rival ambiguity, and whether provenance matches the source. A pass
means only that the sampled lessons resolve the declared independent per-key
quarter-turn family.

`lesson_key_gate.py` can also screen an existing public challenge directly:

```bash
python repo/generators/f2dbde875127/workspace/lesson_key_gate.py \
  solve/challenge.json --out checks/lesson-screen.json
```

It never needs query answers. Unseen keys fail only when the actual query object
admits distinct rival interiors; symmetric queries can pass. Conflicting visible
examples or changed markers/frames are errors.

## Racket differential/key intervention probe

```bash
python run_with_racket.py python \
  generators/f2dbde875127/workspace/key_contrast_probe.py \
  --count 64 --families 16 --phase maintainer \
  --out ../checks/key-contrast-maintainer.json
```

The probe compares unchanged Racket outputs with an independent Python transform
and creates key-only counterfactual families for the first frame. It compares
frame interiors rather than whole outputs, so recoloring the marker cannot fake
semantic dependence. Keep all interventions from one parent input in the same
data split.

## Findings-only audit replay

```bash
python run_with_racket.py python \
  generators/f2dbde875127/workspace/audit_targets.py \
  --out ../checks/audits-replay.json
```

The audit tool refuses changed target hashes. It reproduces a 128/128 count-only
shortcut plus false domain rejection in `40dea3d45f2a`, and 97/768 silently
underfilled rectangle requests in `e4cb0224ca42`. Exit zero means the
investigation completed, not that either target passed. Do not edit those audit
sources in this assignment.

## Next-agent order

Read `REVIEW.md`, `DECISIONS.md`, `RESULTS.json`, `QUESTION_ANSWER.md`, and
`AUDIT.md`; verify source hashes; then rerun the task tests and final probes.
Older failed iterations and the superseded v3.2 lesson are evidence, not current
candidate outputs. Respect solve exposure flags: the fresh solver was not blind,
and visible success does not reveal masked-query correctness. No training run
or admission decision was made.
