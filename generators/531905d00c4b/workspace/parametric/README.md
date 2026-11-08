# Contextual prototype mosaics

Task `531905d00c4b` retains its canonical color-legend decoding rule. This separate
native family adds an episode-fixed `reflection_policy`:

| Setting | Tile operation |
|---|---|
| `canonical` | The exact selected canonical Racket source, unchanged. |
| `larger_left` | Reflect a tight prototype crop horizontally if the decoded left neighbor has more occupied cells than the decoded right neighbor. |
| `larger_right` | Reflect it if the decoded right neighbor has more occupied cells. |

Missing neighbors have mass zero; equal masses leave the tile unchanged.
Reflection happens **before** top-left padding to the common tile size. Every
index token still selects its own prototype. The neighbors determine its
orientation, so two occurrences of one color can have different outputs.

## Dependency and teaching

**A:** split the input at the first blank row, independently crop the legend
objects and the index, then resolve neighboring index tokens to the occupied-cell
counts of their legend objects. **Intermediate:** a color-to-mass map and each
index position's left/right mass pair. **B:** compare those masses under the
episode policy, orient that position's crop, pad, and tile the mosaic.
Comparing color numbers, bounding-box areas, or one cached orientation per color
cannot implement this dependency. The protected native witness records a
wrong-intermediate ablation after qualification.

The first two demonstrations construct opposing contexts for the same token;
shifted/narrow crops; index padding; non-3x3 tiles; both numeric color-order
relationships; and equal occupied masses in differently colored, differently
shaped prototypes. Sparse connected paths and connected dense masks vary shape
structure across seeds. Palettes, legend order, reflections and placements also
vary. Labels, rather than setting-specific input distributions, teach the rule.

The sampler supports **2–6 demonstrations** and **1–4 queries independently**.
The normal native qualification uses three demonstrations and four queries.
Split/slot RNG streams preserve demonstration prefixes and the first query when
counts change. There is no episode rejection loop or silent short batch.
The dense-shape constructor has a bounded 32-attempt connectivity search with
a lawful connected fallback at the same cell count.

Queries progress from a compact index to a large mosaic and a real **30x30 input
and output**. The final input places four 6x6 connected prototypes at
`(0,0), (6,8), (12,16), (18,24)`, covering every library row through 23. Row 24 is
the separator; rows 25–29 contain a dense 5x5 index. The canonical rule crops the
staggered prototypes to 6x6, producing the 30x30 mosaic. These bounds extend the
separate prototype grammar; the production generator's 3–5-row-library validator
is deliberately unchanged. The sampler uses four distinct prototype colors and
a black background, not every possible lawful legend geometry.

## Run from the outer packet folder

Use the passing interpreter from `review.py python-check`; this packet's local
venv is shown below. The wrapper supplies the selected bundled Racket and the
same-checkout Python import paths. On the owner's repository, the equivalent
Python commands need `PYTHONPATH=src:shared/runtime` and the selected Racket on
`RACKET_PATH`/`PATH`. A bare repository-local pytest invocation does not set up
the inherited runtime namespace.

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/531905d00c4b/tests/test_parametric.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/531905d00c4b/workspace/parametric/audit.py \
  --seed 17 --out ../checks/531905d00c4b/audit-new

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  531905d00c4b --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/531905d00c4b/qualification-new --summary
```

The inventory must be current before qualification. `parametric manifest` builds
it from the final prototype and task-local evidence; see the packet's native
promotion guide. Choose fresh audit/qualification destinations after edits.

`audit.py` is the reusable reviewer tool: it executes selected and finite rival
programs in protected Racket, fits rivals on demonstrations only, retains source
hashes and failures, and writes public challenge files from executed labels.
Runtime errors never count as teaching counterexamples. The native qualifier
independently checks the declared settings; the additional semantic rivals are
separate bounded evidence.

## Public/private boundary

`generate(seed, settings, demos, queries)` returns controller-private pairs and
the exact program. Python labels are claims until protected Racket checks them.
`public_turn(episode, i)` is only a projection for the existing controller: it
returns demonstrations and **one** selected query input, without future inputs,
query outputs, settings, seed, program, query index or total-count hints.
It does not implement a turn controller or a training loop.

The audit writes exact `reviewer_support.public_challenge_bytes()` payloads to
SHA-256-named files in `public/`; `private.json` holds answers and programs.
Only public files belong in model inputs. Their IDs depend solely on their exact
visible bytes. The first public turn is identical for one- and four-query uses.

## Sources and status

`adapter.py` loads the adjacent `prototype.py` by exact path. `grid.py` reuses the
pure reconstruction routines from this task's previously reviewed
`workspace/reference_probe.py`, keeping the native dependency closure entirely
inside this parametric home. `canonical.rkt` is an exact copy of the selected
authority text. No production generator, canonical ledger, approval, or shared
runtime source is changed.

Passing tests, the bounded audit, and native qualification support a reviewer
`ready` handoff. They are not owner acceptance, universal identifiability, measured
model learning benefit, or training admission. The owner must integrate and
replay qualification and acceptance on the exact live source.
