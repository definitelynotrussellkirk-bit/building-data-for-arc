# Working notes: 65a142eb4d9b

## Review repair (2026-10-03)

- Replaced v2.0.1's dead/misleading nine-axis surface with four exact observable axes.
- Pinned canonical `RULE_HASH = "7224a7556e4b"`; no Racket authority changed.
- Added finite constructive layout, strict grammar validation, independent mirror/oracle checks, mutation fixtures, semantic witnesses, executable rivals, and lesson identifiability.
- Added a six-profile canonical/isolation/diagonal-edge schedule; every cyclic three-demo window includes all three teaching roles.
- Fixed an intermediate same-color diagonal adjacency bug by requiring the isolation domino to remain Chebyshev distance greater than one from its shared-color singleton.

Final selected generator SHA-256: `813bbc9e683f528b5d7039cca54f528a0706f2d6e4236edd3bb47470c5f99959`.

Final evidence: 12/12 battery stages green, 53 task tests passed, 273 repository tests passed, 300 lessons with zero declared ambiguity, and the independent final probe passed 640 joint override cases plus 180 cyclic lesson windows.

## Explicit limits

The grammar is intentionally narrower than the complete rule domain: at most five expandable cells, one blocked domino, same-color 8-connected groups of at most two cells, and no destructive output-footprint conflicts. The finite rival bank covers the four shortcuts that fit every usable canonical pair; it does not prove uniqueness against all possible programs.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `813bbc9e683f528b5d7039cca54f528a0706f2d6e4236edd3bb47470c5f99959`.

# Decisions for 65a142eb4d9b

## D1 — Preserve the Racket authority

The selected Racket rule already implements the intended transformation: inspect the original grid, expand each nonzero cell lacking a same-color cardinal neighbor into a clipped plus, and leave cardinally connected same-color cells unchanged. The defects were in generation, validation, and curriculum—not the authority. I therefore changed no canonical/base rule data, pinned `RULE_HASH = "7224a7556e4b"`, and required both independent-oracle and live-Racket parity. This resolves F-65-1/F-65-2 without creating a new rule fork.

Rejected alternative: rewriting the Racket to match the old generator's “unique interior dots only” behavior. That would encode a sampling shortcut as semantics and discard valid edge, repeated-color, and blocked-component cases.

## D2 — Replace misleading breadth with four observable exact axes

The v2.0.1 API advertised palette kinds, palette size, cell count, distinct-color count, density, position bias, and texture values that were ignored, fixed, or mixed positive and negative domains. I removed those claims and retained only:

- `grid_h`: 7..10
- `grid_w`: 7..10
- `n_expandable_cells`: 1..5
- `n_blocked_dominoes`: 0..1

Each value is recoverable from pixels through `observe_overrides`; unknown keys and invalid values fail loudly. This makes the contract falsifiable and fixes F-65-1. The final probe exhausts all 4 × 4 × 5 × 2 × 4-band combinations (640 cases).

Rejected alternative: keep legacy axes but mark them diagnostic. They were not useful diagnostics, and leaving them visible would continue to invite silent no-op overrides and mislabeled data.

## D3 — Use deterministic finite construction, not capped retries

Exact joint overrides include dense cases such as five expandables plus a blocked domino on 7×7. The implementation enumerates candidate groups and uses finite backtracking over reserved output footprints, then chooses a compatible domino. It either produces a valid layout or raises a precise construction error; it does not silently return fewer objects after a retry cap.

An intermediate bug placed the shared-color isolation domino diagonally adjacent to its singleton. That merged them into an illegal 8-connected triple. The regression `test_isolation_shared_color_is_remote_from_its_blocked_domino` was written before the source fix; placement now filters same-color domino candidates to Chebyshev distance greater than one from the singleton (F-65-4).

Rejected alternative: random placement with a larger retry count. It would make exact overrides seed-dependent and could still fail or underfill without proving feasibility.

## D4 — Build lessons around three semantic roles

The six-slot schedule is:

1. `canonical_one`
2. `isolation_local_small`
3. `diagonal_edge_small`
4. `canonical_two`
5. `isolation_local_large`
6. `diagonal_edge_large`

With `EXAMPLES_NEEDED = 3`, every cyclic three-demo window contains one role of each kind. Canonical profiles preserve public-shape support; isolation profiles refute “expand all nonzero” and “globally unique colors”; diagonal-edge profiles refute “8-connected singleton” and “interior only.” This repairs F-65-2 at the lesson level rather than relying on aggregate frequencies.

Rejected alternative: independently randomize witnesses. Even high marginal witness rates can leave a particular contiguous lesson with no decisive example.

## D5 — Declare the canonical-fitting rival bank

The four executable rivals are:

- expand every nonzero cell;
- expand only colors occurring once globally;
- treat diagonal same-color contact as connected;
- expand only interior eligible cells.

All four fit all four usable canonical pairs, which is why they are meaningful ambiguity tests. `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS` point to the same executable functions; `lesson_identifiable` rejects a lesson if any competitor survives every demonstration. The semantic gate and 300-lesson census then test the declarations rather than a copied name list.

Rejected alternative: merely document English “rivals.” Non-executable prose cannot prove that a rival fits canonical data or is actually refuted by generated demonstrations.

## D6 — Keep a narrow structural grammar

`self_check` accepts only rectangular ARC-color grids with one to five eligible cells, zero or one cardinal domino, no larger cardinal components, no same-color 8-component above two cells, no different-color cardinal contact, no destructive plus-footprint collision, and at most seven nonzero cells. This is intentionally narrower than the complete rule domain, but every accepted scene is unambiguous and every generated scene is accepted.

Rejected alternative: accept any grid on which the Racket happens to return a grid. For training data, a permissive validator would admit collisions, large components, and scenes whose output can be explained by unrelated transformations.

## D7 — Preserve canonical support in every band

The baseline hard band had 0/20 canonical-profile support. Two schedule anchors use exact public-compatible configurations in every band, producing final exact hits of 7/20 easy, 11/20 medium, and 3/20 hard while still reserving four of six profiles for semantic counterexamples. This repairs F-65-3 without collapsing difficulty to shape alone.

Rejected alternative: make all hard examples large and complex. That creates a band-specific distribution shift where the canonical task profile disappears.

## D8 — Use independent and live authorities in tests

`workspace/reference_probe.py` implements independent scene analysis and rule output; task tests compare the generator mirror to that oracle, while one test invokes the real Racket bridge. `workspace/final_contract_probe.py` exhausts joint overrides and cyclic windows. This avoids testing an implementation only against itself.

The frozen baseline is retained as `workspace/original_generator.py` for diff/reproducer context; it is not imported by the selected generator.

## D9 — Keep audit work findings-only

The drawn audit targets `0f6ba01fa18c` and `59a9a5c505fb` were inspected and probed, but their source was left byte-for-byte unchanged. Counterexamples and sampling evidence live under `checks/audit/`; findings are reported in `AUDIT.md` as A-0F-1 and A-59-1.

## Known limits

The finite rival bank is not a proof against every possible shortcut. The teaching grammar deliberately excludes more than one blocked domino, more than five expandables, same-color 8-connected groups larger than two, and destructive overlapping plus footprints. Those restrictions are explicit and tested; future expansion should add a rival/witness and cyclic-window test before broadening the domain.
