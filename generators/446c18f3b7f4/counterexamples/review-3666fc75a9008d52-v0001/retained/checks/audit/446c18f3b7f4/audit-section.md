## 446c18f3b7f4

**Current exact-control defect reproduced: an admitted request for three frames
silently returns one.** This findings-only audit re-executed the current source;
the two retained `needs_triage` audits were used as leads. Both already cite the
same current source SHA-256
`3564b4dcd16258f2c9f10498446073c2a15f6e721b3ae98ffd140de148a4d995`.

The exact call
`generate(0, 0, difficulty="medium", grid_h=11, grid_w=11, n_frames=3)` returns
an 11 by 11 grid containing **one** hollow green frame. Its inclusive bounding
box is rows 3–8 and columns 2–7, and `self_check` returns `[]`. The retained exact
input has SHA-256
`cc60efceafc6ffb4ca8447c1c164f4ce2d6241b19bd4c2b257457e17c445645b`.
This is an actual generator emission, reproduced by the same call; it is not
a manually manufactured failing input. The requested values lie inside both
the published axes and this difficulty band's actual draw bounds.

The defect is in the placement loop: it stops after 400 attempts and returns
the partial grid without requiring `len(boxes) == n_frames`. The first large
placement in this draw prevents further placements. Capacity is not the cause:
a separately retained 11 by 11 grid contains three valid 3 by 3 frames at
top-left coordinates `(0,0)`, `(0,5)`, and `(5,0)`. These have the generator's
two-empty-cell separation, are not nested, and pass the same validator. The
generator should restart the bounded arrangement or fail visibly when it
cannot realize the requested exact count, rather than return a short result.

**Reference output and domain were checked through the supported Racket path.**
`arcpuzzles apply --check-generator-domain` reports the emitted grid valid and
returns a valid 11 by 11 output that changes exactly four cells from green 3 to
yellow 4: `(3,2)`, `(3,7)`, `(8,2)`, and `(8,7)`. Its output SHA-256 is
`9769701d358682d15b63a73730d91f89e0fe0f36200f2f51ab1eaf7d69a14ee4`.
The feasible three-frame grid is also domain-valid and has exactly twelve
corner recolorings. This is a frame-count contract failure; these checks found
no incorrect reference label and make no semantic-rival claim.

**Two additional current control mismatches were reproduced.**

- The published broad valid ranges do not match admitted overrides. At seed 0
  and index 0, medium `n_frames=6` raises
  `draw_int('n_frames'): override 6 outside [1, 3]`; medium `grid_h=5` raises
  `draw_int('grid_h'): override 5 outside [11, 15]`; and easy `n_frames=2` raises
  `draw_int('n_frames'): override 2 outside [1, 1]`. The axes advertise
  `n_frames=1..6` and `grid_h=5..22`. Separate default draw ranges from accepted
  control bounds, or describe the actual band-specific bounds accurately.
- With the same 11 by 11/count-3 controls, changing `palette_kind` from `warm`
  to `cool` produced identical grids in all four paired seeds 0–3. Changing
  helpful `texture` from `warm` to `cool` also produced identical grids in all
  four paired seeds. The current code never consumes `palette_kind` and only
  uses `texture` for its three degenerate branches. Remove misleading helpful
  controls or make their distinct observable meanings explicit without
  changing the rule's fixed green target color.

**Finite scope and provenance.** The count probe used four medium draws at
seeds 0–3 and index 0; one of four missed the requested count, while all four
passed `self_check`. It ran three documented-control rejection probes and eight
paired helpful-control contrasts. All five labelled canonical pairs were read
through `reviewer_support.canonical_pairs`, passed `self_check`, and matched
fresh Racket execution exactly. Seven reference inputs were executed in total:
the generated witness, the hand-built feasibility witness, and the five
canonical pairs. No task-local `test*.py` file was found, and no full battery,
lesson census, broad seed-rate estimate, private solve inspection, or general
semantic certification was performed. Generator, rule, shared files and
existing review state were left unchanged.

The matching catalog/executed rule hash is `3aceea94fc79`. The executed wrapper
rule-text SHA-256 is
`92466dd221f3f3d3904f10bfd903ab11dcd30d098911fc76a6b1a8cafe8ca4ac`;
the canonical ledger's unnormalized `program_solution` SHA-256 is separately
recorded as `db65c6be2630dd63af4d62d1636c1c6c030a91b439af6bfea4fd94b2a090b39c`.

**Evidence and commands.** Retained files are
`checks/audit/446c18f3b7f4/evidence.json`, `probe.json`, `input.json`,
`input-identities.json`, `racket.json`, `racket-verification.json`, and reusable
`probe.py`/`verify.py`. The process receipts `probe.command.json`,
`racket.command.json`, and `verify.command.json` preserve exact argument arrays,
outer cwd, effective payload cwd and return code **0**. The expected control
rejections are retained as audit observations in `probe.json`; no process run
failed. All commands were invoked from the outer packet through
`WORK/.venv/bin/python review.py run ../.venv/bin/python ...`, with effective
payload cwd `WORK/repo`. The public reference command was:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles \
  apply 446c18f3b7f4 --input ../checks/audit/446c18f3b7f4/input.json \
  --check-generator-domain --out ../checks/audit/446c18f3b7f4/racket.json
```

No generated runtime tree is retained in this audit directory.
