# Native side-boundary family

`adapter.py` exposes the existing side-boundary rule through a constructive
native sampler. The retained `prototype.py` still owns the exact Racket programs
and Python claim semantics; its legacy builder and exporter remain available.
The production generator, canonical authority and approval state are unchanged.

| Episode setting | Side-wall interpretation |
| --- | --- |
| `canvas_edges` (canonical default) | Left/right canvas boundaries count as walls. |
| `gray_walls` | Both sides require literal in-canvas gray columns. |

Both settings discover orthogonally connected black regions, compute each
region's bounding box, require complete gray top/bottom rows, preserve the
multi-row column-zero exclusion, and paint only qualifying component cells
yellow. The default preserves canonical bytes with SHA-256
`e8cf01347e8f1013e5af75c1170767e3bac1afd1974dca142f8ff406e41672bd`.

## Native interface and geometry

`native_family.generate(seed, settings=None, demos=3, queries=4)` supports exact
integer seeds in `0..2**63-1`, **2–6 demonstrations** and **1–4 queries**
independently. Settings are exactly `{"side_boundary_policy": "canvas_edges"}`
or `{"side_boundary_policy": "gray_walls"}`; omitted settings use the default.
`program(settings)` and `normalize_settings(settings)` share that contract.

Every request constructs the same six-demo/four-query bank before slicing.
Input RNG streams do not depend on settings or requested counts. The first two
demos contain large eligible regions, small rejected L-shaped regions whose
complete sides fail, all four wall directions, irregular cell masks, multiple
selected regions, side-edge positives, top/bottom negatives and the column-zero
exception. An identical small L occurs both behind complete walls and beside a
failed bbox side, with opposite labels. This counters shape-only as well as
size-only selection.

Four queries cover an 8×8 scene, a medium scene, a tall or wide scene with one
side of length 30, and a 30×30 scene with content in all four quadrants. Compact
scenes vary their components and wall facts by seed while preserving an interior
positive example. Generation uses bounded direct construction with one attempt
per scene; no rejection loop or silent count truncation is used. Role colors
remain 0/5, with output color 4.

The actual component partition and geometry are required intermediates: changing
four-neighbor grouping to eight-neighbor grouping can merge a rejected L with a
diagonal singleton, change its bounding box, and change the later paint decision.
This is an input-derived geometry dependency, not iterative state simulation.

## Runnable checks and examples

From the packet's outer directory, using its prepared Python environment:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q generators/5f9a2df57599/tests/test_native_wall_family.py generators/5f9a2df57599/tests/test_native_wall_audit.py generators/5f9a2df57599/tests/test_native_wall_export.py generators/5f9a2df57599/tests/test_wall_teaching_gate.py

WORK/.venv/bin/python review.py run python3 generators/5f9a2df57599/workspace/parametric/audit_native.py --out ../checks/5f9a2df57599/audit-new

WORK/.venv/bin/python review.py run python3 generators/5f9a2df57599/workspace/parametric/make_examples.py --seed 0 --demos 3 --queries 4 --out ../checks/5f9a2df57599/examples-new --report ../checks/5f9a2df57599/examples-new-report.json
```

The audit freezes hypothesis survivors from demonstrations before inspecting
queries. It executes complete rules through protected Racket and compares them
with an independent Python implementation. Fifteen named rivals represent
fourteen non-equivalent distinctions per setting: a duplicate enclosure rule
and the strict-policy redundant column-zero exception are documented explicitly.
All retained programs, inputs, outputs, cache counts and source hashes are private
review evidence. This finite check does not prove unrestricted rule uniqueness.

The example builder verifies native claims through protected Racket and retains
the exact native wrapper and full adapter metadata. **Only one
`turns/<hash>.json` file is model-visible per turn.** All-query containers are
under `private/controllers/`; query answers, settings, programs, ordered turn
maps and execution metadata remain private. Visible IDs hash only exact visible
bytes. Existing destinations and duplicate payloads are rejected; publication
writes the completion manifest last. The existing consumer supplies sequencing.

## Reusable cheap teaching gate

```bash
WORK/.venv/bin/python review.py run python3 generators/5f9a2df57599/workspace/parametric/check_wall_teaching.py ../checks/5f9a2df57599/examples-new/private/metadata.jsonl --require-contrast --out ../checks/5f9a2df57599/gate-new.json
```

This opt-in gate reads demonstrations only. It requires a painted region with a
side longer than four, plus the same compact interior shape both painted behind
complete walls and rejected with a failed bbox side. It accepts episode JSON, episode collections and native
metadata JSONL. Apply it to already reference-verified labels: it performs no
Racket execution and grants no acceptance. A task intentionally limited to small
rooms, or a good lesson lacking an exactly repeated shape with opposite outcomes,
can be a false positive.

## Handoff boundary

The native inventory and qualification bind exact source bytes. After integration,
the owner must qualify and freshly accept the integrated source before native
production use. Reviewer-ready status and the native worker's historical
`accepted_parametric` reference marker do not confer owner acceptance or training
admission. Existing production size/distribution audits remain unresolved;
the broader native sampler is a separate proposal. No learner benefit is measured.
