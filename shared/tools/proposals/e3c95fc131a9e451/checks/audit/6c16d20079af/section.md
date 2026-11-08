## 6c16d20079af — validator enclosure gap and two reproduced contract defects

**Findings-only audit; generator and canonical rule unchanged.** The audited generator is `generators/6c16d20079af/generator.py`, SHA-256 `b6e992cf829514f6569d8c22c4d8413ffe7f7ca6aaa0635a12da5a21380fa34a`. The exact canonical `program_solution` UTF-8 SHA-256 is `cd21fd256d4d521e394222197752313d23a61a507ccad5da3e930d1e17703c8a`. The exact task row, including its terminating newline, has SHA-256 `dde37f587f79728f1b22b5c92b095a311954ca6665290e8e62fd917d8c43497f` in `shared/data/canonical/puzzles.jsonl`.

### F1: A one-cell opening removes the required enclosure, but the validator accepts it

The canonical written rule requires an enclosed zero region that is disconnected from the crop border. The Racket function `e5b-fill-holes-key` implements that distinction by rejecting zero regions touching the crop boundary. In contrast, the Python helper `_has_bbox_hole` at lines 213–217 only asks whether an interior bounding-box position is zero. It never tests whether that zero region reaches the boundary.

The exact base call is `generate(0, 0, difficulty="easy", grid_h=11, grid_w=11)`. Its first component is a color-3 rectangular ring occupying rows 1–4 and columns 0–3 (zero-based inclusive); its four interior zeros are enclosed. `input.json` retains this exact generated grid. In `open_ring_input.json`, the only change is `(row=1, column=1): 3 → 0`. This opens the ring directly to its crop boundary. The grid still has the same dimensions, palette, isolated key, component spacing and solid distractor. Independent flood filling finds **zero enclosed targets**, but `self_check(open_ring_input)` returns `[]`.

**Domain and severity:** The base is an ordinary emitted sample with supported exact dimensions. The mutant is an adversarial one-cell change, not an emitted sample. It deliberately violates the semantic hole requirement while retaining the surrounding structural conditions. This is a concrete validator false acceptance, not evidence that normal generation currently emits open rings.

**Fresh public Racket execution confirms the distinction.** The exact generated base returned the expected 4×4 crop with its four interior cells filled with key color 8 (`racket.json`, `valid_output=true`, command exit 0). The one-cell mutant returned `output=null`, `valid_output=false` and `RacketBridgeError: Racket error: map: contract violation; expected: list?; given: #f` (`open_ring_racket.json`, command exit 1). Both receipts bind the same audited generator SHA, executed/catalog rule hash `cd21fd256d4d`, `rule_hash_matches_catalog=true`, and executed rule-text SHA-256 `b80e74c26de7de081dd4eda63effcba5b5b3a3d32d47a5cf61ce7f6d25b51d3b`. The retained receipt inputs match the exact witness files. The invalid mutant is correctly outside the reference domain; the defect is the validator accepting it.

### F2: Canonical solid-before-target examples are rejected; normal generation omits that distinction

Fresh direct calls through public `reviewer_support.canonical_pairs` confirm that canonical `train[2]` and `train[3]` both receive `['first scan-order component is not holed; hole indices=[1]']`. The other three labeled canonical pairs pass. Each rejected pair has a lawful solid component before the enclosed target. `canonical_train2_input.json` and `canonical_train2_expected.json` retain one exact canonical counterexample.

The generator always puts the ring in the top half at line 135 and distractors in the bottom half at line 144; the validator requires `holes[0] == 0` at lines 249–250. Thus it removes the canonical need to skip earlier solid components. A direct sample of 384 exact calls—seeds 0–127, sample index 0, each of `easy`, `medium` and `hard`, no overrides—found no self-check failures and always found the first enclosed target at component index 0. This sample confirms the observed shortcut; the placement code establishes why it persists.

**Status:** This reproduces the currently retained unresolved positional finding on the same source bytes; it is not presented as a new discovery. The canonical examples are authoritative task-domain cases, though they lie outside the generator's narrowed positional grammar.

### F3: The exact `n_solid=3` override is silently ignored

`AXES["n_solid"]` declares integers 1–3 valid at line 66. The exact call `generate(123, 5, difficulty="easy", n_solid=3)` returns the grid in `override_input.json`, containing one holed component and **two** solid distractors, and `self_check` returns `[]`. The returned grid is identical to `generate(123, 5, difficulty="easy")`. Line 125 draws an internal random value in 1–2 instead of consuming the supplied override.

**Status:** This independently reproduces the retained unresolved exact-axis finding on current source. Unlike F1's adversarial mutant, this is an unmodified emitted input from the stated public call. The output can satisfy the canonical transformation while the requested generation contract is still violated.

### Evidence and limits

`probe.py` is the complete repeatable direct-source probe; `probe.json` binds source, canonical row and rule hashes to exact input hashes, recipes, mutation coordinates, validator messages and independent geometry descriptions. `commands.json` records executed commands, working directories and statuses. Reproduce the direct checks from `WORK` with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 checks/audit/6c16d20079af/probe.py
```

The following public reference commands were executed serially from the packet root, with the payload's effective working directory `WORK/repo`. The first exited 0 and the second exited 1:

```bash
python3 review.py run python3 -m arcpuzzles apply 6c16d20079af --input ../checks/audit/6c16d20079af/input.json --out ../checks/audit/6c16d20079af/racket.json
python3 review.py run python3 -m arcpuzzles apply 6c16d20079af --input ../checks/audit/6c16d20079af/open_ring_input.json --out ../checks/audit/6c16d20079af/open_ring_racket.json
```

`racket-commands.json` records the exact executed argument vectors, working directories, exit codes, elapsed times and log paths; `input_racket.log` and `open_ring_input_racket.log` retain the command output. A final direct replay verified the saved reference inputs, exact source/rule bindings and their contrasting outcomes without launching another runtime.

No batteries or staged check suites were launched for this audit because the extracted workspace has inode pressure; the two serialized public `apply` commands provided fresh reference execution. The direct sample found no normal emitted-domain semantic failure; it does not establish exhaustive correctness. Retained historical strict-lint results were read only through the current review index and were not rerun or claimed as fresh evidence. Blind solve labels were not inspected. No approval, audit-resolution or source metadata was changed.
