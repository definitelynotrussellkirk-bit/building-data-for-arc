# Parametric destination-edge family — `96d4a788da47`

The private episode parameter `destination_edge` has three settings:

- `left` — the byte-exact canonical rule;
- `right` — move each object until its bounding box touches the right edge;
- `nearest` — independently move each object to its nearer horizontal edge, with ties going left.

Step A finds every monochromatic connected object and measures its bounding-box
left and right margins. The intermediate is a per-object signed horizontal
displacement selected by the episode rule. Step B translates every original cell
by its object's displacement onto a fresh blank canvas. A constant `+1` shift is
a wrong-intermediate counterfactual and changes the final protected-Racket label.

Inputs are matched across settings and support 2–6 demonstrations plus 1–4
queries independently. Each scene has three differently colored, row-separated,
irregular objects, including one left-near and one right-near object. Query
canvases are 30×30, 24×30, 30×24, and 27×29; the 30×30 scene has at least 24
occupied cells and touches both the top and bottom rows while spanning from
column 1 through at least column 27.

The public-turn helper reveals demonstrations and one input-only query, never the
private setting, program, future queries, or query answers. `audit.py` executes
all intended labels and bounded named rivals through protected Racket. This is
finite source-bound evidence, not proof of universal identifiability or training gain.
