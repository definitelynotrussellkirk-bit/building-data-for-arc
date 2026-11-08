# Aligned or reversed row transfer

This is a separate, runnable **proposed parametric family** for `ec1260207f71`
(original ARC `673ef223`). The production generator and its canonical authority
remain unchanged. Owner qualification and acceptance are still required.

## Rule and input grammar

Two equal red bars occupy opposite side edges in separated row bands. Cyan
markers occur beside exactly one bar. Identify the marked bar, join each marker
to that bar in cyan, turn the marker magenta, then transfer its bar-relative row
to the plain bar and fill that destination row in cyan.

`transfer_order` is fixed for the entire episode:

| Setting | Destination offset for marker offset `k` in a bar of length `L` |
| --- | --- |
| `aligned` (default) | `k`; byte-for-byte original canonical Racket |
| `reversed` | `L - 1 - k`; the join and marker recoloring are unchanged |

The intermediate marker offsets and identification of the plain bar determine
the later fill. This preserves the source task's relational reasoning and adds
a meaningful alternative mapping. It is contextual selection and remapping,
not an iterative simulation.

The separate prototype grammar admits integer grids from 14–30 rows and 7–30
columns, bars of equal length 4–14, at least two rows between their bands, and
1–`L` markers on distinct rows inside exactly one band. Unselected bar offsets
and unused canvas rows remain distractors. Additional colored objects or markers
outside the marked band are unsupported. No arbitrary rotations are advertised.

The unchanged production sampler is restricted to 14–28 by 7–16 with 4–8-cell
bars and at most five markers. The prototype naturally extends the same Racket
geometry to 30×30; its dense maximum case has two 14-cell bars, 12 markers,
top/bottom contacts, and markers near both side edges. The canvas is used for
long bars and long fills, rather than padding a canonical-size object.

## Demonstrations, queries and controls

`generate(seed, settings, demos=3, queries=4)` supports **2–6 demonstrations**
and **1–4 queries independently**. Use three demonstrations and four queries
for ordinary exports. The first two demonstrations constructively cover both
left/right and upper/lower branches; the first uses asymmetric offsets to
distinguish the parameter settings. No rejection sampler or retry loop is used.
Later demonstrations include fuller marker coverage. Inputs use a separate
setting-independent RNG, so the same seed/count request matches across settings.

Queries use four substantive profiles: 14×7, 19×17, 26×24 and 30×30. The last two
use maximum lawful bar lengths. Demonstrations have six separate shape profiles;
this makes all demo/query inputs distinct by construction. These ten profiles
are the sampling support; the validator's larger grammar is not a claim that
every possible shape or scene is sampled. Within profiles the side, row band,
bar length, marker count/offsets and marker columns vary where applicable.

Teaching checks fit **only demonstration inputs and outputs**, against both
parameter settings and seven executable shortcuts: upper-only, lower-only,
left-only, right-only, join-only, transfer-only, and unchanged-marker variants.
The intended rule is the sole survivor for each generated lesson. Every query
is checked against surviving predictions without fitting on its answer. This
finite family is not a uniqueness proof against arbitrary or conjunction-based
shortcuts. The old canonical upper-only audit is retained and is not resolved
by this separate family.

## Run and reproduce

From the outer packet directory, after its normal environment setup:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/ec1260207f71/workspace/parametric/verify.py \
  --out ../checks/parametric/fresh-replay

WORK/.venv/bin/python review.py run ../.venv/bin/python -m pytest -q \
  generators/ec1260207f71/tests/test_parametric.py

WORK/.venv/bin/python WORK/check_public_exports.py \
  WORK/checks/parametric/fresh-replay/examples/public --demos 3 --queries 4
```

Use a new output directory. `verify.py` invokes the native adapter evaluator and
the same checkout's protected Racket bridge. It checks seeds 0 and 17, each setting,
and demo counts 2, 3, 6; independently replays all labels and executable rivals;
compares the teaching certificates; replays the four supplied canonical pairs;
and retains a literal one-marker setting witness. It also checks label/program
tampering, duplicate inputs, boolean cells, forged certificates and first-turn
equivalence. A rival runtime error aborts verification, rather than counting as
a successful disproof. The report records actual runtime and source hashes.

The four retained example episodes use three demonstrations and four queries,
covering both settings and both seeds. `examples/public/` contains canonical
visible-byte SHA-256 filenames with masked query answers. `private.jsonl` and
the Racket programs carry settings, seeds, answers and certificates separately.
The export helper sorts public IDs and rejects duplicate visible episodes.
Its labels remain Python claims until linked protected-Racket replay succeeds.

The public directory is a **controller-side batch store**, not the first user
turn. Existing turn consumers should call `visible_turn(episode, index)`, which
returns the demonstrations plus only the current query input. It includes no
query count, ordinal, future input, program, parameter or private identifier.
For identical seed/settings/demo count, query zero has exactly the same visible
bytes whether generation requested one query or four. No training loop or turn
controller is included.

## Native promotion handoff

`adapter.py` exposes the standard `program(settings)` and
`generate(seed, settings, demos, queries)` interface. `promotion.json` declares
the bounded settings/counts and pins the adjacent canonical Racket resource.
The adapter loads its prototype by exact adjacent file path.

After validation, use the existing manifest helper with the task's retained
`evidence/current` receipt and explicit `tests/test_parametric.py` include. The
inventory records source/evidence bindings, not qualification. Owner-side
`parametric qualify` and `parametric accept` remain explicit later actions.
The existing canonical semantic-contract and authority-text findings remain
open. This package changes no approval, training admission or mixture weights.
