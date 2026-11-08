# Bounded audit of 7a0930447310

This directory contains findings and replayable evidence, not a source patch.
`AUDIT_SECTION.md` is ready to copy into the return's `AUDIT.md` under the exact
assigned task heading. All paths in that section assume this directory is copied
to `WORK/checks/audit/7a0930447310/`.

From the outer packet directory, with its declared Python dependencies installed:

```bash
python3 review.py run python3 ../checks/audit/7a0930447310/probe.py --out ../checks/audit/7a0930447310/replay
python3 review.py run python3 -m arcpuzzles apply 7a0930447310 --input ../checks/audit/7a0930447310/replay/apply-inputs.json --check-generator-domain --timeout 120 --out ../checks/audit/7a0930447310/replay-racket.json
python3 review.py run python3 ../checks/audit/7a0930447310/probe.py --out ../checks/audit/7a0930447310/replay --compare-racket ../checks/audit/7a0930447310/replay-racket.json
```

Use new output names for another run; the probe and supported apply command
refuse to overwrite retained results. If needed, substitute the reviewer
environment's Python executable for the payload `python3` after `review.py run`.

The probe uses `reviewer_support.load_selected_generator` and `canonical_pairs`.
It requires the exact audited source hash and normalized canonical rule hash.
When run outside a packet's `checks/` directory, supply `--root /path/to/repo`.
The `rule_text_sha256` in `observations/summary.json` hashes the canonical JSONL
program string. The same-named field in the stock `racket.json` receipt hashes
the executed rule text as emitted by its runtime. These raw text hashes differ
with formatting; both bind to normalized rule hash `3b7ecb6b00ec`.

The five retained apply inputs are ordered as follows:

| Index | Input origin |
| --- | --- |
| 0 | Canonical variant 0, train pair 0 |
| 1 | Canonical variant 0, train pair 1 |
| 2 | Canonical variant 0, train pair 2; one special center color |
| 3 | Canonical variant 0, test pair 0; 5×5 and cropped frames |
| 4 | Generated override witness, seed 0, sample index 0 |

Canonical indices are zero-based. `summary.json` retains aliases in the second
canonical variant, all sixteen override results, and the exact bounded control
scope. Racket labels are compared with retained canonical outputs only for
indices 0–3; no independent expected label is asserted for the override witness.

The initial Racket attempt used a sparse checkout and failed before executing
the task because a shared runtime file was missing. The successful attempt used
the full original extraction. Both commands and the initial error remain in the
evidence. No generator, shared source, contract, or assignment was edited.
