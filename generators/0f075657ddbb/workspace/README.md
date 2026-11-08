# Review workspace / next-agent handoff

Selected task: **0f075657ddbb**. Assignment: `review-28df04f9d685dce9`.
`../generator.py` is the implementation; this workspace is never automatically selected.

## Use the returned patch

Extract the small review return separately from the original packet. From the original packet root (the directory containing `repo/` and `run_with_racket.py`):

```bash
git apply --check /absolute/path/to/review_return/patches/source.patch
git apply /absolute/path/to/review_return/patches/source.patch
python3 setup_racket.py
mkdir -p repo/var
python3 run_with_racket.py python3 -m pytest -q generators/0f075657ddbb/tests
python3 run_with_racket.py python3 -m pytest
```

The scratch `var/` directory is needed by an existing repository integration test. No shared test/source patch is necessary. Do not apply onto an already modified selected generator without reconciling the source hashes. The return builder checks original assignment identity and confines source modifications to the selected task and bound authority file.

## Source-bound Racket differential probe

```bash
python3 run_with_racket.py python3 generators/0f075657ddbb/workspace/review_probe.py \
  --count 400 --seed-start 20000 \
  --fixtures generators/0f075657ddbb/workspace/fixtures.json \
  --out ../checks/my-fresh-probe
```

Each output path must be new. This means 400 seeds for **each of easy/medium/hard**, always sample_index=0, plus the canonical pairs and fixtures. The script checks repeated generation, input purity, self-check acceptance, canonical labels, optional Python-mirror equality and declared rivals. It labels by the exact canonical Racket source, not by the mirror. Results include `summary.json`, `process.json`, `samples.jsonl`, `canonical.jsonl`, `fixtures.jsonl`, `failures.json` and `rival_witnesses.json`. Source hashes bind the result to the generator and canonical ledger. A failed/timed-out process is not a pass.

To inspect another task without modifying it, pass `--task TASK_ID`. To compare an old generator, pass `--generator /path/to/baseline/generator.py`; it is staged in isolation. `--root /path/to/repo` supports relocation. Pair normalization accepts singleton test objects and digit-string rows. The probe is for ordinary trusted review code, not an untrusted-code security sandbox.

## Real after-policy battery

The public `arcpuzzles check ... --out ../checks/after` currently hardcodes phase `before`. Use the executed workaround from the return, with a new output directory:

```bash
python3 run_with_racket.py python3 /absolute/path/to/review_return/checks/run-strict-after.py \
  --out ../checks/my-fresh-after
```

It stages current sources and runs the unchanged underlying battery with `after --fresh --keep-going`. Read the battery summary and stage logs; an exit-zero advisory is not a green stage. Never update imported approval evidence merely because these local probes pass.

## What changed and why

The Racket rule and canonical ledger are unchanged. Overrides are exact and observable; malformed requests fail explicitly. The sampler mixes compact morphology and broader stress cases. Four-index, seed-conditioned lessons contain first/last/random-rank examples plus a no-op; across seeds both missing and overflow selectors occur. Every four-demo lesson includes a first-rank contrast with a non-prefix selector and protected off-row red. The selected no-op regime repeats within a seed, so an overflow query has an overflow demonstration. This fits the serializer's 2..5-demo contract.

`fixtures.json` contains explicit boundaries, lawful no-op variants, a hand-specified protected-cell output, a thin-frame identity, and invalid combinations. The default sampler still does not routinely emit 2-high inner frames; do not confuse fixture coverage with distribution coverage.

## Continue from evidence, not old intermediate greens

Authoritative final evidence is in the return's `checks/after-release/`, `checks/probe-release/`, `checks/regression-release.log`, and `checks/full-pytest-release.log`. Earlier failed runs are intentionally retained. Read root `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, `AUDIT.md`, and `FEEDBACK_TO_CODEX.md` before further work.

No further rule surgery is justified by this review. A bounded next improvement would be a separately named thin-frame/empty-interior curriculum, with held-out frequency tests and the unchanged canonical Racket reference. Do not broaden this patch into the two other audit targets; they are findings-only assignments with exact reproducers.
