# Native contact-cluster layers — 366cda05b486

The episode fixes `scope=cluster|farthest`; `cluster` is the exact canonical
default. An object is a monochromatic cardinally connected foreground component.
Two objects are adjacent when their cells share a cardinal edge. Find the unique
blue (1) object. `cluster` extracts its entire connected object cluster.
`farthest` computes **shortest object-hop distances** from blue and extracts
**all complete objects tied at the maximum reachable distance**. Crop the chosen
union tightly, recolor its cells 8 and preserve zero gaps. Input cyan is an
ordinary color. Equal-colored disconnected components remain separate objects.

## Dependency and causal intervention

**A** traverses the input-derived contact graph to compute shortest hop distances.
The **intermediate** is the distance assigned to each reachable object. **B**
selects the maximum-distance objects and extracts their complete geometry.
Object size and Euclidean/Manhattan position cannot substitute for graph depth.
The causal counterfactual supplies only blue/immediate-neighbor depths while
leaving maximum-layer selection, cropping and painting unchanged. Unvisited
objects receive depth −1, so the complete program remains defined. This is
graph-derived selection, not a claim about iterative grid simulation or training gains.

## Grammar and construction

Native inputs are rectangular lists with axes 1–30 and exact integer colors
0–9. Exactly one monochromatic cardinal component has color 1. An isolated blue
object is valid; both settings then extract it. Other object counts, shapes,
colors, cycles and disconnected clusters are unrestricted by the grammar.
This explicitly broadens the separate production v2.1.0 restrictions on small
polyominoes, exactly two clusters and a blue leaf. Production code and approval
identity remain unchanged.

`generate(seed, settings=None, demos=3, queries=4)` accepts exact integer seeds
0 through 2**63−1, 2–6 demonstrations and 1–4 queries independently. An omitted
setting is chosen once per episode using a separate deterministic random stream.
Inputs and query ordering do not depend on the setting. Construct the complete
six-demo/four-query bank before slicing; never retry, clone or shorten a request.

The first two demonstrations are complementary constructive cores:

- A seven-object detour has a spatially near, graph-distant L-shaped terminal
  object, repeated colors in distinct objects, selected cyan and a larger,
  more-object-rich distractor touching only diagonally.
- A cycle with a non-leaf blue object has a shallow leaf and two unequal,
  asymmetric terminal objects tied in object hops. Their cell distances differ.
  Cyan is only in the distractor. The farthest output retains both terminal
  objects with intervening zeros.

Each core receives an independent D4 transform and a permutation of colors
`{2,3,4,5,6,7,9}`, fixing blue and cyan. These preserve the semantic witnesses
while varying placement, orientation and ordinary colors. The core template
bank is finite and does not claim uniform sampling of all legal graphs.

Additional fields construct a thick serpentine cluster split into variable-width
monochromatic objects, with repeated nonadjacent colors, optional one-cell
branches and a separate dense distractor cluster. Two-row gaps and end connectors
preserve the route; branches occupy the first gap row away from its connector.
Every loop has a finite geometric bound. The four additional demo dimensions
are 7×9, 15×18, 24×27 and 30×30; queries are 8×12, 18×21, 26×29 and 30×30,
all allowing transposed orientations. The two 30×30 roles use different band
thicknesses, so they cannot coincide. Other roles have different dimension pairs.
All ten inputs are therefore distinct within every bank.

The 30×30 scenes contain hundreds of foreground cells, many monochromatic
objects and deep contact paths spread across the canvas. The final labels
depend on traversing those objects, rather than padding a small source scene.
Legal 1×1 and isolated-seed boundaries are separately covered by literal tests;
the sampled small profile is 7×9. Supported grammar does not imply that every
legal graph or dimension is sampled.

## Checks and commands

`tests/test_native_family.py` checks literal transformations, ties, cycles,
repeated colors, exact controls, mutation isolation, count prefixes, novel
matched inputs and dense/deep 30×30 content. `audit_native.py` has an independent
object parser/oracle and exact executable rivals. Its teaching decisions use
only the first two demos; its label audit checks the full six-demo/four-query
bank for both settings and fixed seeds. Execution errors are failures.

From the outer packet folder, with its selected Python environment:

```bash
python3 review.py run python3 -m pytest generators/366cda05b486/tests/test_native_family.py generators/366cda05b486/tests/test_native_audit.py
python3 review.py run python3 -m arcpuzzles parametric qualify 366cda05b486 --demos 6 --queries 4 --out ../checks/366cda05b486/qualification-new --summary
python3 review.py preview-public export --qualification ../checks/366cda05b486/qualification-new/qualification.json --out ../checks/366cda05b486/preview-new
python3 review.py preview-public verify --bundle ../checks/366cda05b486/preview-new
```

Choose fresh output paths. The current source/evidence inventory is
`evidence/manifest.json`, with actual checks under `checks/366cda05b486/`.
Python outputs are claim labels; native qualification independently executes
every label through protected Racket. Bounded named-rival checks do not prove
universal rule identification.

Reveal one selected `public/<sha256>.json` file at a time. Keep settings, rules,
answers, future query inputs and directory listings with the controller. The
existing exporter supplies the projection; this work adds no turn controller.
Owner native qualification and fresh acceptance of both exact integrated
sources remain separate. No training admission or activation follows.
