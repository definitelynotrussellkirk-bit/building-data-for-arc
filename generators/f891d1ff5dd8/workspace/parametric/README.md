# Marker-derived cycle phase prototype

This task-local native prototype keeps the selected canonical rule byte-for-byte
as the default and adds one nearby episode-fixed setting:

- `cycle_start=first_header` — canonical default. Preserve rows 0–1 and paint
  each body row from the ordered row-0 cycle with phase zero.
- `cycle_start=row1_marker` — find the unique row-1 cell whose color appears in
  row 0, locate that color's unique zero-based index in the header, and use the
  derived index as the phase for every body row.

The alternative has a real sequential dependency. Step A must read the marker
and locate it in the input header. Its derived header index is the intermediate.
Step B consumes that index to choose the first and subsequent body colors. The
protected-Racket counterfactual deliberately substitutes the marker's physical
row-1 column for its header index; the resulting output differs.

## Contract

- deterministic, setting-neutral inputs;
- one private setting for the complete episode;
- 2–6 demonstrations and 1–4 prefix-stable queries;
- qualification uses three demonstrations and four distinct queries;
- the four-query bank includes a substantive distributed 30×30 input;
- public projection exposes exactly one current query, with no setting, program,
  answer, future query, or total-query hint; its ID hashes exact public bytes.

The first two demonstrations constructively distinguish both admitted settings
from each other and from the declared phase shortcuts. `audit_native.py` also
executes seven finite rivals through protected Racket at the 2/3/6-demo count
boundaries. This is finite teaching evidence, not a universal uniqueness or
measured-learning claim.

## Replay

From the extracted packet directory:

```sh
python3 review.py run python3 -m pytest -q \
  generators/f891d1ff5dd8/tests/test_parametric_cycle_direction.py

python3 review.py run python3 \
  generators/f891d1ff5dd8/workspace/parametric/audit_native.py \
  --seeds 0 17 31 --demos 2 3 6 --queries 4 --stress-seeds 64 \
  --out ../checks/f891d1ff5dd8/self-audit/report.json \
  --public-out ../checks/f891d1ff5dd8/public

python3 review.py run python3 -m arcpuzzles parametric qualify f891d1ff5dd8 \
  --out ../checks/f891d1ff5dd8/qualification --summary
```

Native qualification and the causal witness are reviewer evidence only. Owner
acceptance on exact integrated live bytes and any later training admission remain
separate decisions.
