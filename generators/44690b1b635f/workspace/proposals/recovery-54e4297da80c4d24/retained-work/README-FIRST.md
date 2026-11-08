# Read first — ARCpuzzles source-bound recovery overlay

Assignment: `review-efb25880f190b5c1`  
Repair task: `44690b1b635f`  
Blind task: `7c2b3290ba62`

This ZIP is **not** the official `review_response_*.zip`. The original
349,966,246-byte immutable upload was successfully extracted and verified,
but that workspace was later reset. The file service still exposed the upload
while refusing rematerialization above its 100 MB limit. This package therefore
contains a conservative recovery overlay rather than fabricated packet receipts.

## What is implemented

- Generator v3.1.0 retains the canonical 4-neighbor BFS rule and pinned
  `RULE_HASH 72a0e00e932b`, while adding a deterministic, structurally
  validated perfect-maze profile to break the 42-template geometry shortcut.
- A task-local regression suite, independent BFS oracle, malformed-maze
  checks, diversity census, and deterministic/RNG-isolation checks are included.
- A proposed two-axis parametric prototype emits fixed-setting episodes with
  3 demonstrations and 4 distinct queries; alternate Racket execution remains pending.
- The exact recovered blind solver and notes are included, with their original hashes.
- Two future-agent tools are included: hash-bound replay and deterministic
  allocation-audit sampling.

## Safest replay into the immutable packet

Use a **fresh extraction** of the original uploaded ZIP. Replace the example
paths below with absolute paths. The replay tool is dry-run by default and
refuses the wrong assignment, wrong generator preimage, symlinks, unsafe paths,
unexpected overwrites, or any source/hash mismatch.

```bash
BUNDLE=/absolute/path/to/review_recovery_review-efb25880f190b5c1
PACKET=/absolute/path/to/fresh/original-packet-extraction
cd "$PACKET"
python3 review.py verify
python3 review.py start
python3 review.py blind prepare
python3 "$BUNDLE/tools/replay_in_full_packet.py" --bundle-root "$BUNDLE" --packet-root "$PACKET"
python3 "$BUNDLE/tools/replay_in_full_packet.py" --bundle-root "$BUNDLE" --packet-root "$PACKET" --apply
```

The expected generator preimage is:

`bb35eded97d3630896e16b409b8c80dd6f5b7439aa2c00f6f08302740db18356`

After application, replay the already-completed blind attempt through the
official journal before inspecting any repair source in that fresh extraction:

```bash
python3 review.py blind check --intent solve --note 'Panels are separated by all-9 columns; candidates are marked when their occupied cells form a nonempty subset of the pixels added from the first reference panel to the second.'
python3 review.py blind finish --earlier-exposure no --reference-consulted no --reason 'A single structural hypothesis explains all visible examples exactly; the implementation is dimension-generic and the private query labels are intentionally unavailable.'
```

Then run the packet-owned checks (from the packet root):

```bash
python3 review.py setup
python3 review.py run python3 -m arcpuzzles check 44690b1b635f --battery --timeout 4000 --phase after --out ../checks/after-recovery
python3 review.py run python3 -m arcpuzzles check 44690b1b635f --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-recovery
python3 review.py run python3 -m arcpuzzles lesson-census 44690b1b635f --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census-recovery.json
python3 review.py run python3 -m arcpuzzles generate 44690b1b635f --count 1 --seed 17 --test 4 --out ../checks/four-query-recovery.jsonl
python3 "$BUNDLE/tools/sample_allocation_audit.py" --manifest WORK/PACKET-MANIFEST.json --seed d29c972914db3fb8577bd8fa12b00f498c07884908f524cb4d21f015c50be87f --out WORK/checks/recovery/allocation-sample.json
```

The full packet must additionally execute the alternate parametric Racket
programs against retained private labels, complete the visible-only post-repair
solve, run `python3 review.py audit` once and fill both exact audit sections,
update the reports with those results, and finally run:

```bash
python3 review.py package --out review_response_review-efb25880f190b5c1.zip
```

Only that packet-built ZIP is the official submission.

## Local verification without the full packet

```bash
cd RECOVERY-REPO
PYTHONPATH=. pytest -q
```

See `WORK/REVIEW.md`, `WORK/RESULTS.json`, and `PATCH-MANIFEST.json` for
the exact scope, hashes, evidence, and unresolved gates.
