# Translation-only packing family: public_eval_5dbc8537

## Rule and settings
The general reference identifies the modal background, the largest remaining frame color, the target crop, and external solid rectangular multicolor pieces. It backtracks over translated pieces to cover every target hole, preserving the pieces' internal patterns. It uses no supplied-grid or answer lookup. Protected Racket reproduces both original demonstrations and both supplied test labels.

`frame_policy=original` is byte-identical to the authored root reference. `first_placed_piece` solves the same packing, selects the piece covering the first row-major target hole, measures its modal color (lowest numeric color breaks ties), and recolors the frame. Source scan order does not select the downstream color.

## Sampling and teaching
The standalone generator and parametric sampler are byte-identical. Inputs vary inventory count (8 or 9), dimensions, patterns, palettes, source positions, four rotations, and multiple interlocking cavities. Claim construction checks unique final output, allowing harmless permutations of identical pieces. It rejects unsatisfiable or output-ambiguous covers and bounds the Python search.

The native adapter accepts 2–6 demonstrations and exactly four distinct queries. Inputs are identical across settings. Demonstration count changes neither earlier demonstrations nor the independent query bank. The fourth query is substantive 30x30. Public delivery independently shuffles the four-query order and reveals one current query with no setting, program, future input, output or total-count hint.

Expanded auditing found genuine pre-repair teaching failures: source-last and smallest-piece selectors fit two demonstrations but disagreed with a query. Their exact inputs, programs, outputs and twelve protected-Racket evaluations are retained in `checks/public_eval_5dbc8537/teaching-findings.json`. The repaired sampler removes incidental singleton-color and source-endpoint correlations. This is not a claim that every possible alternative is excluded.

## Verification and limits
The task-local suite has 24 passing tests, including all originals, exact-cover failures, equivalent-piece permutations, request bounds, input neutrality, query-bank invariance, diversity, canonical bytes and standalone relocation. A 32-seed audit covers 192 episodes, 1,472 labeled pairs, demo counts 2/3/6 and twelve policies. No harmful named rival survives. Its labels use independent Python claims; separate original, preflight, six-demo boundary and causal receipts use protected Racket.

Authoring preflight passes for two settings x seeds 17/43, two demos and four queries. Forty additional protected labels cover six-demo boundaries at seeds 0/31. Sixteen sequential public views pass byte-identity, masking and first-turn mutation checks. Replacing solved destination selection with the first source piece changes 253 cells on a retained 30x30 query (correct modal color 2, wrong 7); fresh protected replay confirms it.

The general reference assumes a unique modal background, a frequency-dominant frame, separated solid rectangular pieces, and a satisfiable translation-only cover. Arbitrary other grid grammars and exhaustive seed/rule uniqueness are not claimed. The retained official pairs satisfy this interpretation. Sampling currently covers this constructive subfamily, not every possible packing.

## Handoff
This is unregistered authoring work, not an approved generator. `preflight-final` is the current source-bound receipt; preflight is never native qualification. Catalog `task-tests` returns Unknown puzzle until owner registration; complete local and relocated-generator tests pass. Owner registration, native qualification and fresh acceptance remain required; training admission is false. Shared catalog/canonical/runtime files and immutable public-parent provenance remain unchanged.

## Current repeated-parent reconciliation

Retain exact original/first_placed_piece programs and unchanged ordinary sampler; add exact last_placed_piece program and demo-only source-endpoint rejection that teaches solved placement order. Both first/last destinations are taught within two demos. All original query geometry retained; stable private full-bank shuffle precedes 1..4 prefix projection. Named rival audit preserves harmless equivalences explicitly. Current evidence resides in evidence/repeat-fourth-union. Private native acceptance and root publication are separate.
