# Native frame-phase family

Reviewer status: **native qualified; owner acceptance pending**. The selected production generator and canonical Racket authority are unchanged. This family is a separate opt-in extension, with no training admission.

## Rules and grammar

`phase_relation` is fixed for the whole episode:

| Setting | Transformation |
| --- | --- |
| `same` | Exact canonical program: row-major first marker chooses which interior quadrant parity gets its color. |
| `opposite` | The retained guarded phase inversion. |
| `move_then_fill` | Move the original first marker to the first empty cell, scanned row-major, in its diagonally opposite exterior corner; then run the exact canonical fill on that changed grid. |

The moved rule must reread the marker order. Its retained counterfactual performs the identical exterior move but fills from the old marker binding. On the qualified 30×30 witness, the programs differ in all 576 interior cells.

The separate native grammar permits 10–30 rows/columns, a complete gray frame 5–26 cells per side with two-cell exterior margins, a blank interior, and exactly two distinct colored singleton markers in exterior corner regions. Additional colored distractors are outside this grammar. The original generator's smaller domain and validator remain unchanged.

## Supported requests

- **3–6 demonstrations**, default and qualification count 3.
- **1–4 distinct queries**, independently requested; ordinary training uses 4.
- Literal integer seed in `0..2**63-1`; Boolean and coercible values are rejected.
- Input sampling is independent of settings and requested counts.

Three demos are necessary for the declared all-quadrant teaching contract. A two-demo subset lets a column-only phase rule fit both demos and change a later query. The constructive three-demo lesson varies both phase axes, cue color rank, row/column order, occupied relocation targets, and same/opposite cue parity. The first two examples share canvas/frame dimensions to reject a size-based phase shortcut.

Four query profiles cover original first markers in UL, UR, LL and LR. Two are 30×30, with 576 and 506 cells filled; the others are 23×27 and 15×19. Dimensions, quadrant schedules and color-rank schedules are fixed profiles. Seeds vary colors, frame offsets where possible, and some marker positions. This is not exhaustive structural sampling or D4 equivariance.

## Reproduce the bounded audit

Run from the extracted packet's outer folder, using the ready interpreter selected by `review.py python-check`:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/b7c3b8bc9805/workspace/parametric/audit_native.py audit \
  --out ../checks/frame-native-fresh
```

Defaults: all three settings, seeds 0/17, demo counts 3/6, and four queries. The audit checks every label through protected Racket, replays eight canonical pairs, and tests declared parameter/shortcut rivals using demonstrations alone. Returned evidence records 12/12 usable episodes, 102 labels, 236 refuted rival checks, and no harmful survivor in that finite set.

Public files contain one query each and are named by SHA-256 of their exact visible bytes. The first-query file is identical for one-query and four-query requests. Give the model only its current file from `public/`; the controller retains the episode map, future queries, settings, programs and query labels under `private/`. The report is controller metadata. `family.public_query` supplies the same strict projection without implementing a turn controller.

## Native qualification and causal replay

The return includes the adapter, promotion contract, current inventory, and protected qualification/execution records. Produce fresh qualification on the exact integrated source:

```bash
python3 -m arcpuzzles parametric qualify b7c3b8bc9805 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out var/review/frame-qualification --summary
```

The task-local tool selects a qualified moved-rule example and authors a replay recipe; the shared helper verifies both programs and source bindings:

```bash
python3 generators/b7c3b8bc9805/workspace/parametric/audit_native.py witness-recipe \
  --qualification var/review/frame-qualification/qualification.json \
  --out var/review/frame-witness-recipe.json
python3 -m arcpuzzles.review_witness build \
  --qualification var/review/frame-qualification/qualification.json \
  --recipe var/review/frame-witness-recipe.json --out var/review/frame-causal
```

The owner assesses the causal interpretation and accepts exact live bytes through the native promotion API. Reviewer qualification is not acceptance. After acceptance, the standard native exporter supports `--demos 3 --queries 4`.

## Evidence and limits

`evidence/qualified/report.json` indexes the current audit and public/private examples; `evidence/manifest.json` is the native source inventory. The return's `checks/b7c3b8bc9805/qualification/` and `causal/` contain qualification and replay. The task test runner passed 111 tests in an isolated staged runtime. No broader repository battery, model training, allocation change or universal induction claim is made.

`prototype.py` retains the earlier two-setting, fixed-fixture diagnostic API for compatibility. Its fresh public writer now uses exact visible-byte hash names. Historical `evidence/returned/` is prior authoring evidence, not the native export.
