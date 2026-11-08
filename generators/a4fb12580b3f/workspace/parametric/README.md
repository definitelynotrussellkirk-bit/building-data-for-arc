# Anchor neighbors and a selected relay

This separate native adapter preserves the exact canonical `direct` program.
Its other episode-fixed setting, `largest_relay`, binds the largest original
component touching the blue anchor and extends recoloring through that object.
Canonical production code is unchanged. Native owner acceptance remains separate
from this reviewer qualification and from training admission.

## Rule and domain

Find monochromatic four-connected nonzero components in the original input.
The unique color-1 component is the anchor. Let D be the components touching
the anchor by a cardinal edge, and R the unique largest member of D by cell
count. In `direct`, recolor D to 4. In `largest_relay`, recolor D and every
non-anchor component touching R to 4. Stop after that additional hop. An
already-4 component can be R. Do not discover components after repainting.

The sampler supports independent heights and widths of 14..30, 2..6 demos
(ordinary default 3), and 1..4 queries. The four-query dimensions are 30×30,
14×30, 30×14 and 26×28. This is a separate extended distribution; the unchanged
canonical sampler still declares heights 7..15 and widths 8..16.

Input arrays are identical between settings for the same seed/count request.
Queries use a separate fixed stream, so increasing demo count or query count
does not alter the first query. All pairs are distinct. Every grid contains
competing branches, a third-hop continuation, diagonal contacts, a repeated
color distractor and a globally larger disconnected object. The first two demos
put a non-4 relay last in scan order with a smaller already-4 competitor, then
an actually largest already-4 relay first. This refutes both preferring and
ignoring already-yellow relays without adding a demonstration. Larger grids
grow the relay and other objects instead of only enlarging empty background.

## Reproduce from the packet's outer directory

Use the Python interpreter that passed `review.py python-check`; the example
below uses the packet-local environment. All payload paths start at `WORK/repo`.

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/a4fb12580b3f/tests/test_parametric_rules.py \
  generators/a4fb12580b3f/tests/test_parametric_sampler.py \
  generators/a4fb12580b3f/tests/test_parametric_adapter.py \
  generators/a4fb12580b3f/tests/test_parametric_audit.py \
  generators/a4fb12580b3f/tests/test_parametric_export.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/a4fb12580b3f/workspace/parametric/audit.py \
  --seed 0 --seed 17 --demos 2 --demos 3 --demos 6 \
  --out ../checks/a4fb12580b3f/new-audit

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  a4fb12580b3f --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/a4fb12580b3f/new-qualification --summary

WORK/.venv/bin/python review.py run python3 \
  generators/a4fb12580b3f/workspace/parametric/export_qualified.py \
  --qualification ../checks/a4fb12580b3f/new-qualification/qualification.json \
  --out ../checks/a4fb12580b3f/new-examples
```

Choose new output directories. After changing sources or included tests, rebuild
the native manifest using the documented `parametric manifest` command and its
exact old-hash `--replace` guard before qualifying again. The current manifest
lists the full task-local source/test inventory and bounded checks.

## Public and private data

The export's `public.jsonl` and `public/<visible-sha256>.json` contain only demos
and the first query input. Names hash those visible bytes exclusively. The
other three queries, all query answers, mode, seed, program, and source receipts
stay in `private.jsonl` and `manifest.private.json`. The pure `reveal(episode,i)`
helper returns one current query; reveal order belongs to the existing controller.
There is no query index/count hint or future input in a public challenge. The
first public turn is byte-identical to a single-query projection.

`adapter.generate` returns Python label claims. Native qualification independently
executes those claims with protected Racket; `export_qualified.py` consumes the
hash-bound qualification and execution, never unverified adapter output.

## Evidence and limits

The finite self-audit checks 8 direct-mode and 16 relay-mode rivals, including
diagonal contact/components, global recoloring, local-pixel recoloring, wrong
relay selection, preferring or ignoring an already-4 relay, all-branch expansion and recursive
flooding. Fit decisions use only demonstration outputs; query labels are checked
afterward. Successful execution is required for every rival. The retained check
covers seeds 0 and 17 with 2, 3 and 6 demos and four queries.
It is evidence for those finite rivals and draws, not uniqueness against all rules.

The causal witness replaces the selected relay with the second-largest direct
component and executes both programs. This demonstrates a dependency on a
derived object, not simulation of an updated intermediate grid. The retained
canonical seed-73 diagonal-contact audit is still open for the unchanged
production sampler; this extension's constructive lessons address that gap
within the new family only.
