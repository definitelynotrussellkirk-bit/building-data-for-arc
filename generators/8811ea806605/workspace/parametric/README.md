# Column gravity with ordered line clearing

This opt-in family extends task `8811ea806605`; its approved production sampler
and canonical reference remain unchanged. The native adapter exposes one
episode-fixed parameter:

| `mode` | Transformation |
| --- | --- |
| `fall` (default) | Exact canonical Racket program: count blue cells per column and bottom-pack them. |
| `fall_then_clear` | Bottom-pack, then remove every full blue row from that result and prepend empty rows. |
| `clear_then_fall` | Remove full blue rows from the input, prepend empty rows, then bottom-pack. |

Rows and columns retain their original dimensions. The rule grammar accepts
rectangular binary grids from 5×5 through 30×30, including empty grids and grids
whose every row clears. The sampler deliberately supplies nontrivial examples.
There are no foreign-color distractors: black and blue retain the source rule's
roles. Source positions, counts, gaps, boundary contacts and densities vary.

## Teaching and size support

`generate(seed, settings, demos, queries)` supports **3–6 demonstrations** and
**1–8 independently chosen queries**. Use three demonstrations and four queries
normally. Invalid counts, unknown settings, booleans and inexact cell values are
rejected. Each slot has its own deterministic input RNG; private settings and
requested counts cannot change a slot's input.

The mandatory demonstrations contain:

1. Three full input rows, including both border rows, but seven full rows after
   gravity, with unequal column counts. This distinguishes the three modes and
   exposes multiple-row and boundary-row clearing.
2. A genuinely empty column and a nearly full row. These prevent clearing and
   expose shortcuts that ignore empty columns or accept almost-full rows.
3. One full input row and two after gravity. This rejects a fixed positive
   clearing amount inferred from the first demonstration.

The three-demo minimum preserves those three cases. Two demonstrations would
leave a useful count or no-clear distinction untaught; the adapter rejects that
request rather than emitting a weaker lesson. Optional demonstrations add variety.

The first four query profiles are 5×5, 12×17, 21×27 and 30×30. They cover no original
full rows, empty columns, several full rows, and dense boundary-spanning content.
The 30×30 scene contains a full-height column and content in every row and column;
it is not an enlarged empty border. The unchanged production sampler remains at
5–12 rows, 5–14 columns and at most four blue cells per column. Larger counts and
canvases belong exclusively to this separate parametric family.

## State dependency and its limit

For `fall_then_clear`, A is column gravity; its intermediate is the packed grid
and its newly formed full rows. B removes those rows. An input with `k` original
full rows and minimum column count `m > k` yields different answers when B reads
the original grid instead, or when the operation order is reversed.

This composition also has a compact histogram formulation: for column counts
`c[j]`, the three output heights are `c[j]`, `c[j] - min(c)`, and `c[j] - k`.
The witness establishes a meaningful dependence on the updated state, not a
claim that a solver must carry out an irreducible simulation. Zeroing full rows
before gravity is equivalent to physically removing them before gravity, and is
not a wrong-rule rival in this domain.

## Run the focused tests and build review examples

From the outer extracted packet directory, with its configured Python:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/8811ea806605/tests/test_parametric.py

WORK/.venv/bin/python review.py run python3 \
  generators/8811ea806605/workspace/parametric/audit.py \
  --out ../checks/8811ea806605/self-audit
```

Use a fresh output directory. The evidence builder executes actual Racket labels,
checks declared wrong-rule alternatives against demonstrations only, and writes
hash-named public examples separately from private settings, programs and query
answers. The audit is finite evidence, not universal rule identifiability.

The public four-query containers are **controller data**. To show one model turn,
call `public_view(episode, query_index)`; it contains the original demonstrations
and exactly one query input. The controller reveals later queries only after the
preceding answer. This projection exposes neither the query index nor the planned
count, future inputs, settings, program or query answers. A one-query episode and
a four-query episode have identical first-turn bytes for the same seed/settings
and demonstration count. No training loop or controller is added here.

## Native promotion

After the focused audit, build the source/evidence inventory, then qualify:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric manifest 8811ea806605 \
  --evidence generators/8811ea806605/workspace/parametric/evidence/current \
  --include generators/8811ea806605/tests/test_parametric.py \
  --reported-checks 'Replace with the actual checks and their limits'

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 8811ea806605 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/8811ea806605/qualification --summary
```

The default program must equal the canonical source byte-for-byte. Native
qualification independently executes every selected label and all declared setting
alternatives through protected Racket. Preserve sibling `execution.json` with
`qualification.json`. A current inventory and passing qualification are review
evidence; they do not grant acceptance.

After integrating exact source, the owner must freshly qualify and accept it
using the existing native API. The returned causal witness also requires owner
replay under the packet's main-admission policy. Training admission remains a
separate downstream decision.
