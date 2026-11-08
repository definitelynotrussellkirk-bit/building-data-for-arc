# Current implementation: contour assembly and depth selection

Unapproved public parent `16b78196`; owner registration, native qualification and exact-source acceptance remain pending. No training admission.

Canonical rule: find the connected full-span wall, orient it horizontally, and translate the remaining monochrome pieces without independent rotation. A nonflat leading contour must meet one complete predecessor interface. Backtrack locally valid dead ends until every piece is assembled. Return the preserved wall and moved pieces, removing source copies. All two training labels and the supplied test gold match protected Racket.

Alternative `highlight_deepest` uses the complete assembly's predecessor map to derive attachment depth, then recolors the deepest class to 9. Its counterfactual substitutes loose-piece area. The generic reference is independent of sampler signatures and source locations.

Sampler: fresh column-convex profile chains; one/two sides; 2..4 attachment levels; widths 5/6; arbitrary colors except reserved 9; all D4 transforms; randomized source placement. Native lessons use 2..6 demonstrations and exactly four queries. The stress query is 30x30 with seven pieces, two chains, substantial wall occupancy and a four-step chain. Inputs match across settings. Explicit impossible width/depth/canvas combinations fail rather than truncate.

Fixed, with failing regressions retained: greedy placement depended on loose-piece reading order; the original test needed one complete predecessor interface; post-rotation source-order proxies survived small teaching prefixes; a valid two-piece explicit production draw was overconstrained by a teaching-only placement condition. The teaching prefix now checks visible and wall-aligned source order using a finite placement search. Queries do not inherit teaching-only position exclusions.

Evidence: checks/public_eval_16b78196/preflight-return and audit-return; 47 tests; 18 bounded audit jobs; 138 label comparisons / 61 unique protected evaluations; fresh two-program causal replay; 256 census episodes; 16 private-controller sequential views; 24 hidden-field invariance mutations. The initial failed audit is retained as superseded evidence, not counted as passing.

Limits: references fit all supplied labels but are inferred rules, not proof of the intended rule on arbitrary unseen inputs. Sampler support is straight, axis-convex chains, not branching or rotation-on-docking. Python assembly search has a 20,000-node failure bound. Finite declared rivals are not universal uniqueness. Final review is author self-review (no independent subagent tool).

Test harness: the combined task suite passes 89 tests. Test modules use unique names to avoid pytest import collisions. Catalog-bound `review.py task-tests` cannot resolve either unregistered public task, so no native task-test receipt is claimed; use the documented direct pytest and isolated relocation commands until owner registration. The frozen repository archival suite also has missing-catalog failures; it was not changed.
