# Enclosed-area selection: native review candidate

This separate family extends `56f043832ecb` without editing its production
generator or selected reference. The default setting returns the exact selected
canonical Racket source, including its whitespace.

## Rule

| `selection` | Transformation |
|---|---|
| `all` | Fill every component's enclosed zero cells with its own color. Exact canonical default. |
| `largest` | Compute each component's total enclosed area, then fill every eligible component tied for the maximum. |
| `smallest` | Compute each component's total enclosed area, then fill every eligible component tied for the minimum. |

A component is a same-color, four-connected nonzero object. Its hole mask is
computed on its **component-only bounding box**, using four-neighbor reachability
from zero cells on that box's boundary. Area sums all its enclosed cells, across
all cavities. Objects with no enclosed cells are ineligible for either extremum.
Disconnected objects with the same color remain separate candidates.

This preserves the canonical algorithm's particular semantics. On arbitrary
legal grids it can paint over a different-colored object nested inside a hollow
component. The sampler avoids nesting and contaminated cavities; it does not
reinterpret the selected reference as a global-background flood fill.

### Required dependency

A discovers each object's enclosed-cell set and computes its total area. The
input-dependent intermediate is the component-to-hole-mask/area mapping. B uses
those computed areas to choose the extremal components, then paints only their
holes. Wall size, bounding-box size, the number of cavities, and the size of the
largest cavity can select different objects. The protected causal witness uses
a qualified input and a wrong intermediate while leaving the hole masks and
paint operation intact.

This is a derived measurement controlling selection. It is not presented as an
iterative simulation that repeatedly updates the grid and discovers new objects.

## Native API and supported requests

```python
program({"selection": "largest"})
generate(seed=17, settings={"selection": "largest"}, demos=3, queries=4)
```

`adapter.py` exposes those functions. The limits are **3–6 demonstrations** and
**1–4 queries independently**, with exact integer seeds in `0..2**63-1`.
Booleans, floating-point values, unknown settings, extra keys, and unsupported
counts fail explicitly. `settings=None` deterministically chooses one of the
three settings using `seed % 3`; it does not always select the canonical default.

Every call constructs a six-demonstration/four-query input bank before taking
prefixes. Inputs match across settings. Query ordering is shuffled once per seed,
independently of the selected setting and requested counts, so the first query
is identical for one-query and four-query calls. All ten inputs must be distinct.
Every return is fresh; no process-global random state is changed.

The first three demonstrations include contrasting total areas, extrema ties,
thick walls, multiple cavities, leaking objects, irregular shapes and repeated
colors across separated objects. Constructive placement puts both a minimum-area
and a maximum-area winner strictly inside the canvas, while their tied partners
touch its border. A later demonstration also selects an interior concave minimum
and an interior multiple-cavity maximum. The rule is therefore taught on both
location classes without increasing the three-demonstration minimum.
The four queries include small and medium
scenes, a larger scene and a substantive 30×30 scene. The separate sampler's
geometry extends the production generator's narrower rectangle/one-spur grammar.
All coordinates and colors remain within the standard 1–30, 0–9 grid limits.

## Source layout

| File | Responsibility |
|---|---|
| `native_family.py` | Strict API, exact canonical default, alternative programs, Python claim mirror. |
| `sampler.py` | Constructive, seed-controlled geometry and shared input bank. |
| `adapter.py`, `promotion.json` | Existing native promotion interface and bounded settings/count contract. |
| `audit.py` | Protected labels, finite semantic rivals, private evidence and public export verification. |
| `canonical.rkt` | Exact selected source, copied through `Catalog`. |
| `evidence/manifest.json` | Native source/evidence inventory made by the existing manifest helper. |

The Python mirror supplies claim labels to the adapter. It does not certify
them. The standalone audit and native qualification independently execute the
materialized programs through protected Racket. Errors fail a check; they are
never counted as successful rival refutations.

## Reproduce the review checks

From the extracted packet's outer directory, using its prepared Python:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/56f043832ecb/tests/test_native_adapter.py \
  generators/56f043832ecb/tests/test_native_audit.py

WORK/.venv/bin/python review.py run python3 \
  generators/56f043832ecb/workspace/parametric/audit.py run \
  --out ../checks/56f043832ecb/audit-new

WORK/.venv/bin/python review.py run python3 \
  generators/56f043832ecb/workspace/parametric/audit.py verify \
  ../checks/56f043832ecb/audit-new/export
```

Use new output directories. The audit's private records retain exact programs,
settings, seeds, input grids and executed outputs. Finite rival checks establish
only the tested distinctions; they do not prove uniqueness against all programs.

After preparing a current task-local evidence inventory:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  56f043832ecb --demos 3 --queries 4 \
  --out ../checks/56f043832ecb/qualification-new --summary
```

The source/evidence manifest, qualification and its sibling execution receipt
must bind the exact final source. Source edits require a fresh inventory and
qualification. Existing protected witness helpers build and replay the bounded
causal case from a selected qualified pair; see the packet's parametric guide.

## Public/private boundary and handoff

The prototype writer exports each query as a separate public challenge with the
same demonstrations and exactly one query input. Filenames and IDs hash only the
exact visible bytes, using `reviewer_support`. Hidden settings, seeds, programs,
query answers, query ordinals and future inputs stay private. The first public
turn is identical for one-query and four-query evaluation. A serialized export
verification is a schema/hash/projection check, not another Racket replay.

This return is a **review candidate**. Reviewer qualification does not grant
native acceptance or training admission. After integrating the exact source,
the owner must run the native qualification/acceptance handoff. Accepted native
exports use the existing controller's sequential-query handling; this prototype
does not add a training loop or controller.
