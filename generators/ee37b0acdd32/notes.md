# Working notes: ee37b0acdd32

## 2026-10-04 review-c65531805f6642cd

The imported v3.1.0 generator was not source-bound and its straight-band sampler did not guarantee the declared graph semantics. An independent 360-sample audit reproduced 55 non-tree contact graphs, 6 multiple-shortest-path scenes, 86 paths outside the canonical 4–6 component range, and 179 branch-contract failures; the validator accepted these emissions. It also declared dead controls and accepted the disconnected `no_chain` fixture.

Version 4.0.0 constructs an induced component-contact tree, validates that structure independently from painting, and exposes only exact observable controls. Three deterministic schedule profiles cover the canonical size/palette signatures in every three-sample window and carry executable witnesses against `paint_all_nonzero`, `keep_multicell_and_endpoints`, and `global_color_union`. The Racket authority was not changed; `RULE_HASH` pins it at `5db437049d2b`.

The first after battery caught a transformation-presentation defect: random inputs reused output color 8, so only 23/60 samples visibly introduced the result color. The final sampler reserves 8 for output. Final evidence is source-bound to SHA-256 `1cf46183d36979212fc84956fecef9801427d54d7072f54559edf358a6953747`.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `1cf46183d36979212fc84956fecef9801427d54d7072f54559edf358a6953747`.

# Decisions: ee37b0acdd32

## D1 — Treat the task as a component-contact graph, not a painted band

**Decision.** The generator now constructs a graph whose vertices are monochrome 4-connected components and whose edges are orthogonal contacts between differently colored components. It then requires that graph to be one tree with a unique blue(1)-to-red(2) path.

**Why.** The Racket rule and canonical examples operate on the chain of touching objects. The imported v3.1.0 implementation instead sampled a straight row of blocks and attached optional pixels; an independent pixel-level audit showed that those pixels frequently merged, made cycles, disconnected the scene, or failed to create real branches. The baseline report `checks/root-cause/before-contact-graph.json` records 55 non-trees, 6 multiple-shortest-path scenes, 86 invalid path lengths, and 179 branch-contract failures over 360 emissions.

**Rejected alternatives.** Tightening the old rejection loop would preserve accidental straight-band geometry and make control behavior hard to prove. Generating an arbitrary abstract tree and solving a free-form packing problem would add complexity without useful lesson diversity. A small constructive induced tree makes every contact intentional and keeps replay deterministic.

## D2 — Construct first, validate again from pixels

**Decision.** Generation uses templates and branch-placement constraints to avoid unintended adjacency, but `self_check`, `rule_mirror`, `observe_overrides`, and strictness checks independently extract components and rebuild the contact graph from the final grid.

**Why.** Construction code and analysis code can share a mistaken assumption. Re-deriving semantics from pixels catches merges, extra contacts, disconnections, endpoint shape errors, path multiplicity, and fake branches. The separate workspace tool `contact_graph_audit.py` repeats that analysis without calling the candidate's private `_analyze`, so the final claim is not circular.

**Rejected alternative.** Returning generation metadata or trusting requested overrides would make the validator pass malformed grids and would not test the artifact learners actually see.

## D3 — Keep only four exact public controls

**Decision.** Public axes are `grid_h` 8–14, `grid_w` 10–16, `path_len` 4–6, and `branch_count` 1–2. Every legal value is observable from the emitted grid and exact under overrides.

**Why.** The imported metadata exposed `position_bias` and texture choices that were either unprobed, behaviorally dead, or overlapping the degenerate domain. A control contract should describe recoverable behavior, not internal sampling knobs. Boundary combinations were generated for all three difficulty labels and independently observed in `checks/final/contact-graph-audit.json`; the repository override stage is also green.

**Rejected alternatives.** Keeping cosmetic controls merely to increase axis count would produce false diversity. Widening path or branch counts beyond the canonical 4–6 and 1–2 ranges would change task difficulty and weaken canonical likeness without evidence that it helps.

## D4 — Use a three-profile deterministic schedule

**Decision.** Consecutive samples cycle `straight`, `elbow`, and `zigzag` profiles, with difficulty only rotating the starting profile. Their default `(height,width,path_len,branch_count)` values are `(8,10,4,1)`, `(10,11,5,2)`, and `(10,13,6,2)` and their exact palette counts reproduce canonical signatures 6, 7, and 8.

**Why.** Every three-demonstration window should cover the three canonical presentation regimes rather than leaving coverage to chance. A period-three schedule makes all cyclic starts cheap to test, gives exact replay, and guarantees one profile with each key witness. The independent audit checked 36 complete lesson windows; the lesson census rotated all 1,200 labelled pairs as queries.

**Rejected alternatives.** IID profile sampling can produce homogeneous lessons and cannot guarantee witness coverage. A single maximally complex profile teaches the rule but poorly matches the canonical distribution. Encoding many near-duplicate profiles would increase surface area without defeating new shortcuts.

## D5 — Build explicit witnesses against executable rivals

**Decision.** The generator declares and tests three rivals: paint every nonzero cell, keep multi-cell components plus endpoints, and keep all components whose colors appear on the route. The elbow/zigzag layouts include a singleton route component, a multi-cell dead-end branch, and a route color reused by an off-path component.

**Why.** The last two rivals fit every usable canonical pair, so merely matching canonical examples does not show that a lesson identifies the graph rule. Each complete generated lesson refutes all declared rivals, and `lesson_identifiable` checks the actual demonstrations/query rather than a witness-name checklist. `checks/lesson-census.json` reports 300/300 lessons refuting every declared rival.

**Rejected alternatives.** Shape variety without executable rivals gives no measurable teaching claim. A global unique-color convention would make color membership itself the answer and preserve the shortcut the repair is meant to eliminate.

## D6 — Reserve color 8 for outputs

**Decision.** Generated input objects use colors 3, 4, 5, 6, 7, and 9 in addition to endpoint colors 1 and 2; color 8 appears only in the transformed output.

**Why.** The first repaired battery found that input color 8 was already present in 37/60 samples, so the output introduced no new color in those cases and the generic transformation-drift gate failed. A test was added before changing the palette, then the final battery was rerun from the new source. The failed intermediate evidence remains under `checks/after/`; final evidence is under `checks/after-v2/`.

**Rejected alternative.** Weakening the drift gate would hide a real presentation problem. Recoloring pre-existing 8 components during transformation would make color semantics part of the rule and diverge from the Racket authority.

## D7 — Do not modify the Racket authority or canonical examples

**Decision.** The Python generator pins `RULE_HASH = "5db437049d2b"`; no base solution or canonical row changed.

**Why.** The defect was in sampling and validation, not the reference transformation. Canonical inputs are accepted and reproduced exactly by `rule_mirror`, Racket rule smoke is green, and authority-sync execution parity passes. Changing the reference would turn a generator repair into a task-definition change.

## D8 — Preserve failures as evidence, not just final passes

**Decision.** Retain the failing baseline audit, the interrupted baseline battery material that completed before timeout, and the first post-repair battery that caught output-color reuse.

**Why.** The repair is easier to trust when each change is tied to a reproduced defect. The baseline source remains byte-for-byte in `workspace/generator_before.py`, and the reusable audit can run against either source.

## D9 — Keep audit targets read-only and answer the data-value question with a shared gate

**Decision.** `08294dfb28a0` and `c6980153fd28` were audited but not patched. Their exact generator/rule hashes, inputs, Racket outputs, rivals, and replay commands are retained under `checks/audit/`.

**Why.** Both defects are lesson-level ambiguity, not malformed single inputs. The higher-leverage shared response is a query-conditional ambiguity gate that tests whether any reference-lawful rival fits all demonstrations and changes the query; for finite symbols it should synthesize alternate mappings for query symbols absent from demonstrations. This is detailed in `QUESTION_ANSWER.md` and prioritized as F1 in `FEEDBACK_TO_CODEX.md`.

## Known limits

The final audit is finite. Nine hundred unique default emissions, exact boundary controls, all cyclic schedule windows represented by the deterministic period, and 300 rotated-query lessons provide strong evidence but do not prove the absence of every imaginable shortcut. The macro geometry comes from three template families, so a learner can infer the profile from dimensions/palette; the included witnesses ensure that profile identity alone does not determine the output. No approval or training-admission metadata was changed.
