# Working notes: 827c34fc8e04

## Current decision

The base generator is repaired and kept canonical. Calls now reject non-exact seed/sample/axis values, invalid difficulty, and unknown overrides. The four-profile lesson schedule covers northwest extension, southeast extension, and two off-axis multi-anchor scenes; every held-out member of the tested four-draw windows remains identifiable from the other three across easy, medium, and hard bands. The six deliberately wrong transformations are lesson competitors only, not canonical shortcuts.

The selected authority record was synchronized to the byte-exact canonical Racket program; archival raw code was preserved.

## Parametric family

The finite family has exactly two settings. `all_markers` is the byte-exact canonical default. `max_color_marker` scans the markers, selects the highest-valued marker with row-major tie-breaking, carries its coordinate and NW–SE diagonal offset as the intermediate, doubles the complete input, and paints color 1 only on that selected diagonal. Inputs are setting-independent and count-prefix independent; the fourth query is 15×15, producing a 30×30 output.

## Verification retained

- Native generator battery: 12/12 green with strict rotation identifiability on generator SHA-256 `bf422eb40599864e118e22e1f3b710f3fc72d1aa5348aedbd0a42354ac4fd0c5`.
- Focused tests: 12/12 passed.
- Adversarial family probe: 10 episodes, 100 labelled pairs, zero findings.
- Protected Racket family worker: four jobs and 40 Racket evaluations, with the intended setting the sole finite survivor in every episode.
- Authoring preflight: four jobs across both settings; 24 parametric labels plus all four canonical pairs; status passed.
- Sequential witness: protected-Racket replay passed and the all-markers wrong-intermediate ablation changed the final output.
- Public projection: four qualified episodes exported as 16 independent one-query views and verified without exposing private settings, programs, future queries, or answers.

## Remaining policy step

No reviewer-side failure remains. Owner-side exact-source qualification/acceptance and any training admission are intentionally still pending; the next useful action is the owner's native acceptance replay against the packaged source and evidence inventory.
