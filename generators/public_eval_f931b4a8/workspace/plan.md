# Count-sized two-scale compositing implementation plan

Goal: implement the exact public parent without a lookup, with a complementary periodic-background setting.
Architecture: Python quadrant extraction/counting/oracle and seeded sampler; one canonical Racket resource; alternate program changes only backing-grid indexing; adapter and reusable bounded audit/export tools.

- [x] Add failing tests for every original label, a hand-derived two-scale fixture, invalid requests and source bytes.
- [x] Implement quadrant counts, coarse backing expansion and nonzero stencil overlay; add matched-input sampling with 2–6 demos and 1–4 independently shuffled queries.
- [x] Adversarially audit pixel-count versus span/count shortcuts, layer priority, transpose, background sampling and crop boundaries. Retain and fix any concrete surviving rival.
- [x] Run complete task tests, source-bound authoring preflight, shared protected causal witness and public export checks.

Grammar: even square inputs up to 30×30, four equal quadrants, 1..30 nonzero cells in each upper quadrant, arbitrary lower quadrant colors and stencil holes. Output dimensions equal the two counts; square quadrant geometry bounds all coarse indexing. Generated domains include mixed-color counters and partial tiles. Input colors are not dimensions.
Review focus: count versus color/occupied rows; transparent zero stencil; coarse versus fine indexing; partial repeated tiles; output dimensions up to 30; deterministic private query shuffle and visible-only exports.
Decisions: alternate sampling changes only the lower-left background from block-expanded to periodically repeated. The canonical dependency already requires an input-derived backing grid before overlay. No production catalog changes or owner acceptance claims.
