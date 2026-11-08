# Reproduced mirror-contract counterexamples

These are authoring evidence, including exact Racket outputs and rival predictions.
Coordinates are zero-based. They are not public challenge files.

`minimal-witnesses.json` records three defects in generator 3.0.0, SHA-256
`d90880567da7d2f2f8f49659fca648c072d2fb941def67ef1de7bb0e2d84cc0a`:

1. An outside yellow mark makes both validation hooks index a reflected column outside the canvas.
2. A geometrically off-center frame is insufficient evidence against whole-grid reflection: both rules can make exactly the same edit.
3. Easy seed 2, consecutive indices 0–3, query position 2 leaves a center-recoloring rival consistent with every demonstration.

`orientation-intermediate-witness.json` records a genuine intermediate repair failure:
easy seed 2, windows starting at 4 and 5, query sample 5. A top-to-bottom rival
fits the three demonstrations but changes the query. Intermediate source hash:
`4ed08f875dd6149aaeb1dd15aff530e5fcc87668a8abef13fdaa5440514bc83f`.

The earlier 3.1.0 source, SHA-256
`992bc69af4dcc2734a08775cdbe855c15a291ff4b8e70d5eb72b8282215194ee`,
returns grammar errors before indexing, tests actual rival disagreement, alternates
occupied/axis teaching branches, and reserves both global-axis and direction-rival
preimages during ordinary draws. The regression tests and independent probe cover
these examples. Full command receipts and failed iterations are retained in the
review return's `checks/diagnosis/`.

`search-warnings-992bc.json` records the next actual failure: four rotated lessons
admit nearest-blue-frame rivals. The input-only predicates exactly reproduce the
shared searched mutations on all 16 saved pairs. Source 992bc is preserved in the
return for replay. The final source SHA-256 is
`437d19653cc59e2bac06cd40ab0f31685edf5488a82060e35d96f95e9b0ef35f`.
Its ordinary axis scenes put a productive target one step from an axis yellow and
at least two steps from any blue border, so both nearest-frame tie policies fail.
`tests/test_nearest_object_regressions.py` records all four failing windows.
