# Arch-support parametric candidate

**Blocked by one immutable original label.** The implementation is runnable and
its generated checks pass, but normal authoring preflight fails on train[1].
Read ../../notes.md for the exact cell, primary sources, semantics, limits and
owner correction workflow. Do not present this folder as an accepted family.

## Interface

- program({"support_mode": "both" | "either"}) returns a complete Racket rule.
- generate(seed, settings, demos, queries) returns train/test pairs and the rule.
- demos: exact integer 2..6; queries: 1..4; seed: 0..2**63-1.
- The canonical default is byte-identical to ../../reference.rkt.
- Input sampling is matched across settings. Complete banks precede prefix
  selection, and the four queries are shuffled using a separate keyed stream.
- Generator and Python simulation come from the admitted task-home base module;
  the Racket resource canonical.rkt lives inside this native folder.

Both settings erase all header-selected colors and settle independent arch
posts and interior beams. A beam is held laterally by both neighbors in the
canonical mode, or either neighbor in the alternative. Collision and iteration
rules are identical. Python labels are claims; the protected runtime owns
verification.

## Commands from the packet's outer folder

Run with the packet's Python 3.12 environment and bundled Racket:

    WORK/.venv/bin/python review.py run python3 -m pytest -q generators/public_eval_b6f77b65/tests
    WORK/.venv/bin/python review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_b6f77b65 --root . --out ../checks/public_eval_b6f77b65/preflight-new

The first command has one strict expected failure for the known label. The
second must currently exit nonzero. Fresh output directories are required.

Private candidate diagnostics, which do not replace preflight:

    WORK/.venv/bin/python review.py run python3 generators/public_eval_b6f77b65/workspace/parametric/audit.py --out ../checks/public_eval_b6f77b65/audit-new/audit.json
    WORK/.venv/bin/python review.py run python3 ../checks/public_eval_b6f77b65/check_candidate.py --out ../checks/public_eval_b6f77b65/candidate-new
    WORK/.venv/bin/python review.py run python3 ../checks/tools/boundary_probe.py --task public_eval_b6f77b65 --out ../checks/public_eval_b6f77b65/boundary-new.json
    WORK/.venv/bin/python review.py run python3 ../checks/tools/public_original_diagnostics.py --root . --task public_eval_b6f77b65 --out ../checks/public_eval_b6f77b65/originals-new.json

The final command deliberately exits nonzero after reporting all original pairs.
Only a selected file under a diagnostic bundle's public/ folder is a single
visible turn. Keep the bundle, directory listing, private reports, settings,
programs, answers and future inputs away from model-visible evaluation.

The owner must correct and rebind the original source before unchanged
preflight, registration, source review, native qualification and acceptance.
The required source inventory is produced by successful native preflight; this
blocked candidate does not manufacture one.

