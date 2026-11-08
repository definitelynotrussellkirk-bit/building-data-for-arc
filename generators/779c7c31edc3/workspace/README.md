# Reusable, source-bound review probes

These tools change no other task. Run from the extracted **packet root**, after
`python3 setup_racket.py`. The wrapper changes cwd to `repo`; `../checks/...`
therefore names the packet evidence directory. Use fresh output names to preserve
older results. No model or network access is required.

```bash
python3 -m pytest -q repo/generators/779c7c31edc3/tests
python3 run_with_racket.py python3 -m arcpuzzles check 779c7c31edc3 --battery --timeout 4000 --phase after --out ../checks/rerun
python3 run_with_racket.py python3 generators/779c7c31edc3/workspace/qualify.py --out ../checks/qualification-rerun.json
python3 run_with_racket.py python3 generators/779c7c31edc3/workspace/replay_gate.py --task 779c7c31edc3 --out ../checks/replay-rerun.json
```

## `probe.py`

Loads a chosen source module, reads canonical pairs, independently checks input
components, and executes authoritative Racket in one relocated runtime. Its
four-neighbor oracle is independent of the production generator and only valid
on the stated solid-monochrome-rectangle domain. It is not a fallback labeler.

## `qualify.py`

Materializes real `runner.run_one` lessons, including runner filtering, with
three demonstrations and one query. It evaluates the actual generator's
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` declarations, checks all canonical
shortcut fits, and verifies claimed witnesses against Racket labels. A trace-only
wrapper counts accepted/unaccepted generation attempts without changing outputs.
It reports finite-rival survivors, harmful query ambiguity, independent parity,
unique-input counts and exact generator/rival/rule identities.

Defaults: 100 pinned lessons per band plus seeds 0–39 at each of the three cyclic
starts per band. These 660 windows contain 2,640 pair occurrences, not necessarily
unique inputs. Per-band pinned seeds use the existing semantic gate's hash-derived
seed policy and starts `k*11`; full policy is in the JSON. A nonzero exit means a
surviving rival or probe failure. Actual temporary runtime path is recorded.

To compare the immutable baseline using the current declared rivals:

```bash
python3 run_with_racket.py python3 generators/779c7c31edc3/workspace/qualify.py --generator ../.review/baseline/repo/generators/779c7c31edc3/generator.py --out ../checks/qualification-baseline-rerun.json
```

The baseline is expected to fail. Measured-generator and rival-source hashes are
separate, so do not mistake the final rivals for baseline declarations.

## `replay_gate.py` — automatic, task-independent rival

Builds `canonical_lookup_else_identity` from all public canonical pairs. A full
lesson fails when that deliberately limited memorizer matches every demonstration
but gives a wrong query output. A replay-only lesson with a replay query is not a
hard failure. Conflicting public labels fail closed. Exact input replay and unique
demo counts are reported separately.

Unlike a raw-draw inspection, this uses actual `runner.run_one` duplicate filtering
and three demonstrations / one query. Seeds 0–99, start 0, all three bands by
default. Full harmful lessons, Racket labels, rival predictions, validator results,
source hashes and attempted sample indices are saved. Exit 1 indicates harmful
ambiguity or a probe error, never simply that an audit completed.

```bash
python3 run_with_racket.py python3 generators/779c7c31edc3/workspace/replay_gate.py --task b7e4aaffabac --out ../checks/replay-audit-rerun.json
```

On the reviewed audit source this reproduces seeds 19, 73 and 95 in each band,
with three distinct demonstrations and a novel changed query. It is a diagnostic
finite-rival gate, not a claim about actual model memorization or contamination.
To reuse it for another catalog task, change `--task`; inspect domain and lesson
policy before interpreting a failure. Stored canonical examples may be legitimate
anchors; require at least one fresh informative demonstration, rather than banning
all canonical overlap.

## `audit_targets.py`

Findings-only probes for assigned tasks `99d5bc858270` and `b7e4aaffabac`:

```bash
python3 run_with_racket.py python3 generators/779c7c31edc3/workspace/audit_targets.py --out ../checks/audits-rerun --lessons 100
```

This tool checks **raw** consecutive draws (sample indices 0–3), not runner
filtering; never promote its lesson counts to exported-lesson counts. It saves
canonical validation, all unique Racket executions, shortcut frequency and small
source-bound counterexamples. Exit 0 means probe completion, not clean targets.
Use `replay_gate.py` for the actual-runner replay finding.

## Return and next ZIP

The delivered ZIP is a delta: read `REVIEW.md` and apply `patches/source.patch`
from the packet root (its paths include `repo/`), or use `git apply -p2` from
an existing repository root. Run `git apply --check` first. Keep assignment IDs and
frozen fixtures unchanged. Re-run the exact verification commands in `RESULTS.json`
before accepting; no automatic training approval is asserted. For a subsequent
round retain this complete return externally, include its filename and SHA256 in
the new handoff, and send a newly assigned review packet with the patched source.
Do not copy old solve evidence onto changed generator bytes or discard failed
iterations. The packet's `package_return.py` should build the next compact return.
