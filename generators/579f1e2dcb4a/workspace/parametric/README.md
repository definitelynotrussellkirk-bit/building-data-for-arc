# Native component-crop packing family

This prototype extends task `579f1e2dcb4a` without changing its production
generator or canonical rule. `adapter.py` loads `native_family.py` by its exact
adjacent path. `sampler.py` supplies inputs only. The adapter's Python outputs
are claims; the audit and native qualification execute the programs through
the protected Racket backend.

## Rule and admitted inputs

All policies find nonzero four-connected components, ignoring color. A crop
is the original rectangular input subgrid inside a component's tight bounding
box. It is **not masked to that component**: pixels belonging to another
component inside the box remain visible, and may be copied again in that
other component's own crop. Crops are packed horizontally, top aligned, with
one zero column between them.

| `pack_order` | Crop ordering |
| --- | --- |
| `spatial` | Original `(left, top)` ascending; exact canonical source |
| `anchor_color_ascending` | Count of the selected color ascending, then `(left, top)` ascending |
| `anchor_color_descending` | Count of the selected color descending, then `(left, top)` ascending |

For both alternatives, first select the unique largest component by number of
occupied cells. Its unique modal nonzero color is the selected color. Count
that color in each component's **own cells**, not in its raw crop. The selected
color is input-dependent, and must be known before the counts and resulting
order can be computed. Descending order does not reverse the spatial tie-break.

The shared input grammar admits rectangular lists of literal integers 0–9,
with both sides from 1 through 30, two through six components, a unique largest
component, and a unique modal color in that component. Other component sizes
may tie, and singletons are lawful. Packed output width must be at most 30.
Bounding boxes may contain other components. The canonical program itself is
preserved byte for byte; these restrictions describe this prototype's sampler
and Python claim API.

## Teaching and diversity

Three demonstrations are the supported minimum. They expose, respectively:

1. A largest component whose selected-color count is not extreme, with
   conflicting area, bounding-box, perimeter, global-color, and monochrome
   selectors.
2. Absolute color counts that disagree with color fractions, and conflicting
   geometric selectors.
3. A nested foreign component, different component/crop histograms, and a
   diagonal same-left tie that distinguishes four-connectivity and tie order.

The first three selected colors differ within an episode. Geometry is reflected
only along axes that retain its teaching role, and colors are permuted per
pair. Extra demonstrations use independent query-profile draws. Four queries
cover two components, a canonical-like split motif, six components, and dense
30×30 packing. The last case has 460 occupied input cells, touches all four
input boundaries, and produces a 30×30 output with meaningful top alignment.

The generator supports 3–6 demonstrations and 1–4 queries independently. It
constructs all six plus four inputs before selecting prefixes. Local SHA-derived
RNGs isolate seed/split/slot/retry; a 64-attempt duplicate bound prevents unbounded
generation. No settings or output labels enter the input sampler.

## Reusable audit and public export

`audit.py` checks exact canonical bytes and all five official pairs, independently
replays labels, screens complete executable rival programs on the first three
demonstrations, and examines queries for surviving rivals. It executes every
screened demonstration even after an earlier refutation. A crash, malformed
grid, or timeout is an audit error, never a refutation.

Public turns contain the visible input/output demonstrations and exactly one
query input. Settings, programs, query answers, future queries, and turn-count
hints remain private. The exporter writes public records in opaque-ID order;
its verifier checks canonical serialization, private associations, file hashes,
missing and orphan records, and exact public projection. Negative regression
tests exercise those boundaries. This is a task-local tool, with no imports
from another review checkout.

Run from the outer review packet (payload cwd is `WORK/repo`):

```sh
WORK/.venv/bin/python review.py run python3 -B -m pytest -q \
  generators/579f1e2dcb4a/tests/test_native_adapter.py \
  generators/579f1e2dcb4a/tests/test_native_audit.py

WORK/.venv/bin/python review.py run python3 -B \
  generators/579f1e2dcb4a/workspace/parametric/audit.py \
  --out ../checks/579f1e2dcb4a/audit-new --seed 0 --seed 17
```

Use new evidence paths after source changes. Refresh the native inventory and
qualification after changing bound code or resources. The return's
`WORK/RESULTS.json` names the final source inventory, execution evidence, and
causal witness. Finite audits establish only the tested cases and rival family;
reviewer readiness does not grant owner acceptance or training admission.
