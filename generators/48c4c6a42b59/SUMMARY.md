# 48c4c6a42b59

An 11–13 by 11–13 zero-background grid contains two or three separated, distinct-color, 4-connected objects. Each object has 6–11 cells in a 3–5-cell tight bounding box and is asymmetric under left-right reflection.

For each object independently, keep all original cells and add their horizontal reflections inside that object's own tight bounding box. Objects do not use the canvas as their reflection frame, and different objects' transformed footprints do not collide.

The generator uses four deterministic curriculum profiles: canonical square morphology, mixed bounding-box aspect ratios, object-size contrast, and a palette counterexample. It declares eight semantic witnesses and eight executable rival rules.

Kind: `per_puzzle`. Version: `3.0.0`. Rule hash: `cecf4f1691f5`.

Review validation on 2026-10-02: 12/12 official battery stages green; 8/8 focused task tests passing; 120/120 Python/Racket parity; 29/60 exact canonical-profile hits and 34/60 envelope hits; semantic gate 121/600 strict with 8/8 witnesses and 12/12 identifiable lesson windows.
