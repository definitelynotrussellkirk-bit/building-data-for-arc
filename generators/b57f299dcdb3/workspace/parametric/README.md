# Plus census: color or complete winning objects

This opt-in family adds `readout=winner_color|winner_pluses` to task
`b57f299dcdb3`. The default returns the selected canonical Racket source
byte-for-byte. The second setting counts complete yellow-centered pluses,
infers their unique modal petal color, then retains every complete plus of that
color on a zero canvas of the original dimensions. Texture, isolated winning
pixels, incomplete yellow crosses and crosses without a yellow center disappear.

The production generator and canonical authority are unchanged. This family has
its own expanded grammar; its inputs need not pass the production generator's
narrower `self_check`. Qualification is reviewer evidence. The owner must qualify
and accept the exact integrated source before native export or training use.

## Teaching and causal dependence

The first two demonstrations share one input except for the four petals of one
complete plus. In scan order, their abstract petal sequences are
`B B A C A A` and `B B B C A A`. The winner changes from A to B. Under the object
readout this changes the retained status of other, untouched pluses. Object
selection therefore consumes the computed census; a fixed color or the first
repeated color cannot replace it.

Both scenes contain misleading global color frequency, incomplete crosses,
non-yellow centers, and loose pixels of the competing colors. A third ordinary
demonstration normally adds different geometry. Counts from 2 through 6 are
supported; four distinct queries use independent streams and are unchanged by
the requested demonstration count. Inputs are also identical across readouts
for the same seed/count request. Only labels differ.

The sampler supports 4–10 complete pluses with count patterns including
`(2,1,1)`, `(3,2,1)`, `(4,3,1)`, and `(4,3,2,1)`. Multiple repeated colors prevent
“find any repeated color” from replacing plurality. Petal and background colors
are sampled from 1–9 excluding yellow; zero is texture, and yellow marks
candidate centers. Background and census maxima are unique. Ties are outside
the admitted grammar, rather than relying on Racket hash iteration order.

## Dimensions and controls

The demonstrations include 12×12, 15×18, 18×15 and canonical-scale layouts.
Four queries progress through 16×20, 20×22, 24×28 and 30×30 (rectangles may be
transposed). The final scene contains ten true pluses, partial/non-yellow
lookalikes, and distant winning pluses touching opposite canvas boundaries.
The object output spans the full 30×30 canvas; its added area carries objects.
The scalar default correctly retains its 1×1 answer.

`prototype.sample_input(seed, height=..., width=..., counts=..., boundary=...)`
is an authoring probe for dimensions 12–30. Motifs occupy separated 3×3 slots;
an overfull request fails explicitly. This helper is not a production override.
The native adapter supports exactly `demos=2..6`, `queries=1..4`, and integer
seeds `0..2**63-1`; booleans, unknown parameters and out-of-range requests fail.

## Run from the outer packet directory

Use the already checked Python interpreter; the commands below assume the
packet-local environment described by START-HERE.md.

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/b57f299dcdb3/tests/test_parametric_b57f299dcdb3.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/b57f299dcdb3/workspace/parametric/check_family.py \
  --out ../checks/b57f299dcdb3/self-audit-new

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  b57f299dcdb3 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/b57f299dcdb3/qualification-new --summary
```

The source inventory must be current before qualification. Its existing
`evidence/manifest.json` records exact source and task-local proof hashes.
After owner integration and exact-source acceptance, the native export is:

```bash
python3 -m arcpuzzles parametric export b57f299dcdb3 --count 2 --seed 73 \
  --demos 3 --queries 4 --out var/datasets/plus-census
python3 -m arcpuzzles parametric verify-export var/datasets/plus-census
```

## Public and private data

Native and audit outputs keep settings, program text, seeds and query labels
private. A controller receives all four private queries, then exposes only the
current query with the demonstrations. Public files have opaque IDs from their
exact visible bytes. The first-turn bytes equal a one-query request, and changing
hidden metadata or a query answer does not affect that public ID. The audit's
per-query files are separate reveal payloads, not one combined model prompt.
No training controller or mixture is changed here.

## Scope of evidence

`check_family.py` is a reusable bounded learnability probe. It fits declared
rivals to demonstrations only, reports any surviving rival's query agreement,
checks protected Racket labels and small/large supported boundaries, and retains
one executable wrong-census witness. Python rival comparisons are explicitly
separate from executed Racket gold labels; the global-frequency Racket rival is
also replayed. Finite tested rivals do not prove universal identifiability.

The repaired legacy test loader exposes a pre-existing authority mismatch:
base solution `raw_code` and `target_code` differ from the selected canonical
program. Those assertions and source files are preserved. See the portability
evidence and task notes; a passing parametric qualification does not resolve it.
