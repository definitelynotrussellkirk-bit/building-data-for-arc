# Current notes: 061566027b67

Canonical generator v3.0.0 and its largest-solid-rectangle Racket authority remain unchanged. The extension is a proposed task-local prototype, with no variant approval or training admission.

## Parametric extension

`workspace/parametric/rectangle_modes.py` retains rectangle selection, coordinates, noise rejection and attached-tab removal. `shape_mode=solid|outline` controls rendering; `paint_color=None|1..9` preserves the source color or paints a fixed nonzero color. The default materializes the exact original program. There are 20 settings.

The first two demonstrations use thick 3x3 and 3x4 winners with attached tabs and different source colors. This distinguishes solid from outline and source color from any fixed color. The certificate exhaustively eliminates the 20 declared settings with demonstrations only, then checks agreement separately for every query. It does not certify arbitrary programs or all possible shortcuts.

Counts are independently configurable: 2..16 demonstrations and 1..16 queries. Four queries cycle the four existing rectangle profiles. All inputs in an episode must be distinct; exhaustion of the 64-attempt per-input retry budget raises. The domain stays 16x16 with the original density, palette, unique-maximum and tab constraints.

The seed-42 evidence uses the same seven inputs across the 20 settings for controlled comparisons: 20 distinct visible challenges, 140 labeled pairs and 80 query outputs, not 140 independently sampled inputs. Broader input diversity requires additional seeds.

The writer uses the shared exact visible-byte projection for hash-only public names, sorts by public ID and rejects duplicate visible challenges before writing. Settings, seeds, programs, certificates and query labels remain under `private/`. The writer projects already-built episodes; it is not itself a reference-label validator. Reusable saved-export, corruption and rejection probes are retained under `checks/` in the return.

## Evidence and limits

Final focused unittest: 7 tests passed. All 20 settings have a complete 3-demo/4-query Racket-backed episode. Min/max counts, deterministic replay, 27 adversarial rejection/contract checks and two saved-export corruption checks passed. Exact commands, source identities and earlier failures are retained in RESULTS.json.

No production battery was run for this prototype-only change. Canonical safety status is inherited, not inferred from this extension. Next useful work is maintainer review of the task-local proposal and, if desired, a bounded additional-seed teaching sample.
