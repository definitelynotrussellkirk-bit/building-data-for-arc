## d9f6e69efb45

**Finding: two independently reproduced generator-contract defects. Audit-only target left unchanged.**

Audited generator version `2.0.0`, SHA-256 `46f76938a6c2e32a047f5e3db58df3c927802f7831d42210220c713717363f49`; selected canonical Racket rule hash `1603ebb35068`. The supported authority receipt matches that generator hash and reports four valid executions. These findings concern generation and validation; no reference-rule bug is asserted.

### AUD-D9-001 — Exact frame count is silently underproduced

`generate(0, 0, difficulty="medium", grid_h=8, grid_w=11, n_frames=2)` returns an 8×11 grid with **one** complete gray frame, bounding box `(0, 2, 4, 6)` (zero-based, inclusive). The public generation context records and consumes `n_frames=2`, while `self_check` returns `[]`.

The placement loop at `repo/generators/d9f6e69efb45/generator.py:94–105` stops after 80 attempts and returns whatever frames fit its random choices. It neither completes the requested count nor rejects underproduction. The validator only requires at least one valid frame. This lets a returned example disagree with its explicit control and recorded provenance.

The request is geometrically feasible. A retained 8×11 control places 4×4 frames at `(0, 0, 3, 3)` and `(0, 6, 3, 9)`. It passes the same validator and satisfies even the implementation's double-padded separation condition. Racket fills both frames correctly. Thus this reproduction is a packing failure, not an impossible dimension/count combination.

Evidence: `checks/audit/d9f6e69efb45/probe.json` records the exact draw and consumed controls; `input.json` index 0 is the generated counterexample and index 3 is the constructive feasibility control. `counterexample.json` includes both inputs, authoritative outputs, hashes, and findings. Scope: one deterministic generated reproduction at seed 0/sample index 0, with the exact overrides above; no failure-frequency estimate.

### AUD-D9-002 — The validator rejects canonical narrow frames, which normal generation never teaches

All **3 public canonical inputs** were checked. `self_check` rejects **both training inputs**, each with `color-5 component is not a complete rectangular frame`; it accepts the canonical test input. The rejected frames are complete gray rectangles with width 3, present in the task's own demonstrations.

The cause is `_is_rect_frame` at `generator.py:160–169`, which requires both outer sides to be at least 4. Normal placement at lines 96–97 also samples both sides only from 4 to 5. The selected reference instead accepts frame heights and widths of at least 3. The generated family therefore omits a positive branch already required by the canonical demonstrations, and its validator incorrectly labels those demonstrations malformed.

The supported Racket command reproduces the exact published outputs for both training inputs. An executable rival that fills only frames with both sides at least 4 fails on those same inputs: it misses 2 filled cells in training pair 0 and 1 in training pair 1. This is a directly witnessed domain/teaching gap; no claim is made that the rival fits every canonical example.

Evidence: `checks/audit/d9f6e69efb45/input.json` indices 1 and 2 are public canonical training pairs 0 and 1. `racket.json` contains the authoritative results and source binding; `rival_output.json` and `counterexample.json` retain rival predictions and exact differing cells. `audit_probe.py` contains the independent frame observer and rival.

### Reproduction and scope

Run `.venv-review/bin/python -B checks/audit/d9f6e69efb45/audit_probe.py` from `WORK`, then use the outer `review.py run python3 -B -m arcpuzzles apply d9f6e69efb45 --input ../checks/audit/d9f6e69efb45/input.json --out ../checks/audit/d9f6e69efb45/racket.json` command with the review environment on `PATH`. Run `.venv-review/bin/python -B checks/audit/d9f6e69efb45/finalize_audit.py` from `WORK` to validate the receipts. Exact argument arrays, relative working directories, exit codes, and evidence paths are in `checks/audit/d9f6e69efb45/commands.json`.

This was a focused audit of one generated exact-control reproduction, all three public canonical inputs, and one packing-feasibility control. Four retained inputs were executed through the public Racket command. No broad battery or exhaustive override sweep was run. The target, selected rule, and shared files were not edited, and no blind/post-repair private solve labels were read. Both findings remain unresolved.
