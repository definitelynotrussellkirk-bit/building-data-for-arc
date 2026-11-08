# Review tools and reproducible commands

The selected implementation is `../generator.py`; workspace tools are opt-in and never selected automatically. Run the following from the **packet root** containing `repo/`, `setup_racket.py` and `run_with_racket.py`. Each evidence output path must be new.

## Tests and canonical battery

```sh
python3 -B -m pytest -q repo/generators/c2b9484357c1/tests
python3 setup_racket.py
python3 run_with_racket.py python3 -m arcpuzzles check c2b9484357c1 \
  --battery --phase after --out ../checks/new-after
```

The wrapper changes into `repo/`, hence `../checks` for its commands. Direct workspace tools do not change directories. Python 3.12+, numpy, Pillow and pytest are the packet's documented dependencies. Racket is required for new reference labels, not for replaying the emitted-lesson gate on saved labeled episodes.

## Canonical-Racket distribution census

```sh
RACKET_PATH="$(python3 -c 'from setup_racket import ensure_racket; print(ensure_racket())')"
python3 repo/generators/c2b9484357c1/workspace/measure_distribution.py \
  --library repo --seeds 32 --racket-path "$RACKET_PATH" \
  --out checks/new-distribution-after
```

This checks all three canonical pairs and 512 generated pairs: seeds 0–31, all four scheduled indices, and None/easy/medium/hard. Outputs include `report.json`, all reference-labeled `pairs.jsonl`, and first counterexamples by rival/difficulty. Python predictions are compared with Racket; they do not supply labels.

For the original snapshot in the same assigned packet:

```sh
python3 repo/generators/c2b9484357c1/workspace/measure_distribution.py \
  --library repo --seeds 32 --racket-path "$RACKET_PATH" \
  --generator .review/baseline/repo/generators/c2b9484357c1/generator.py \
  --out checks/new-distribution-before
```

Expected return code: original 1 because three canonical-consistent rivals survive; revision 0 on this campaign. The tool freezes the three added hypotheses for both versions. Shape multisets ignore color, placement, canvas and each component's D4 orientation; they are a diagnostic, **not** a universal ARC equivalence or an automatic train/test partition rule.

## Actual emitted-episode gate

First generate **private labeled research data** with canonical Racket, explicitly allowing the existing unapproved status:

```sh
python3 run_with_racket.py python3 -m arcpuzzles generate c2b9484357c1 \
  --allow-unapproved --count 2 --seed 17 --difficulty medium \
  --train 4 --test 1 --out ../checks/new-four-demo.jsonl
python3 repo/generators/c2b9484357c1/workspace/validate_lessons.py \
  --library repo --episodes checks/new-four-demo.jsonl \
  --out checks/new-four-demo-gate.json
```

The counterpart with `--train 3` and different output paths is a reproducible negative test at these seeds: both episodes are rejected. It is not sufficient to verify separate synthetic four-demo lessons and then export only three of them.

`validate_lessons.py` loads trusted local generator contracts from the explicit library, requires generator-source and rule provenance, checks every query, checks named rivals independently, rejects mutation/malformed grids, and produces a JSON receipt. Runtime/module imports resolving from another library are rejected. Use a fresh process when changing libraries or source snapshots.

Exit 0 means every actual episode passed the declared contract; exit 1 means semantic/provenance/grid failure; exit 2 means missing contracts, malformed JSON/envelopes or infrastructure failure. A missing hook is reported as `no_contract`, never a pass. The tool does not label new examples, validate an unlabeled evaluation set, provide a code sandbox, or grant approval. It has not been wired into shared export code. Apply it after trusted Racket labeling and before hiding query outputs from a model.

## Limits and evidence

The revision still uses four backbone families and conditional stretching, not unrestricted random objects. It retains a four-demo schedule and 25% strict anchors. Duplicate raw scenes remain. Finite rival coverage and the census are not a model-level generalization result.

The review return includes the before/after batteries, 1,024 matched Racket-labeled generated pairs, red/green regression logs, actual export/gate receipts, and two findings-only audits. The separate broad repository suite's two short-budget subprocess failures are explicitly retained in `REVIEW.md`; they were not patched or hidden by the passing task suite.
