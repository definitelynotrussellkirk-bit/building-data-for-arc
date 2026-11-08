# Reconstruct the hidden patch, then extract its largest object

This separate prototype keeps `output_mode=patch` byte-for-byte identical to
the selected canonical Racket program. `output_mode=largest_object` first
reconstructs the hidden 5×5 patch, then selects its unique largest same-color
four-connected nonzero component and returns that object in its tight bounding
box, with other cells black. Reconstructing the actual patch is necessary to
choose the component; this does not reduce to a per-cell color substitution.

The canonical generator and reference remain unchanged. The prototype reuses
its symmetric fields and injects patch values by full-grid reflection orbits.
This permits nearby multicolor recovered patches while preserving even sides,
one blue 5×5 occluder, at most one crossed axis, and visible symmetry. Tied
largest components are excluded from the admitted sampled grammar.

## API and teaching contract

`adapter.program(settings)` returns the exact Racket text;
`adapter.generate(seed, settings, demos=3, queries=4)` returns private
`train`, `test`, and `program_solution` fields. The Python outputs are claims;
use the native API or the verifier below to execute their Racket authority.

`settings` must contain only `output_mode`, with value `patch` or
`largest_object`. Seeds are exact integers in 0..2^63-1, demos 2..6 and queries
1..4; booleans and floating-point counts are rejected. The chosen setting is
fixed across all pairs. Unique-largest inputs avoid teaching a tie convention;
the executable selector's otherwise-total fallback picks the first row-major
component on a tie and returns [[0]] on an empty patch.

Two jointly selected band demonstrations refute all 23 declared mode/rival
comparisons (7 for patch and 16 for largest_object). Rivals include partial or
unoriented reconstruction, the other setting, first/last/smallest components,
foreground cropping, failure to isolate, 8-connectivity, merging colors,
most-frequent color and bounding-box-area selection. Candidate generation is
independent of the setting, with at most 256 patch attempts per band. Failure
is explicit; no shorter or underidentified lesson is emitted.

Three demonstrations and four queries are the ordinary request. All settings
share their inputs for a fixed seed/count request. Demonstration/query streams
are separate, so the first query is unchanged if evaluation stops after one.
The two mandatory demos cross different center axes; additional demos include
a canonical-style anchor. Four query profiles include 24×24, 20×28, 26×30,
and 30×30. Output dimensions remain at most 5×5 because the puzzle asks about
the occluded patch; this family is not a large-output-data repair.

## Runnable verification and export

From the packet's outer folder, use the Python interpreter that passed
`review.py python-check`. Choose new output paths on reruns:

```bash
python3 review.py run python3 -m pytest generators/f283b8535697/tests/test_parametric_symmetry.py -q
python3 review.py run python3 generators/f283b8535697/workspace/parametric/verify_and_export.py --out ../checks/f283b8535697/audit-d2 --seeds 0 17 --demos 2 --queries 4
python3 WORK/check_public_exports.py WORK/checks/f283b8535697/audit-d2/turns --queries 1 --demos 2
```

The verifier executes every label and rival with protected Racket, checks
demonstration-only identification, samples all four size endpoints, and tests
the actual disk writer's identifiers and public/private separation. It refuses
an existing output destination and publishes only after all checks pass.

Give a model only one selected `turns/<visible-content-hash>.json` at a time.
`controller_public/` is a controller-only complete query batch, despite its
use of the public projection format. `private.json` contains the ordering,
settings, reference programs and answers. Neither settings nor answers nor
future queries nor a final-turn hint appear in a model turn. The first turn's
exact bytes are identical for a one-query and a four-query request.

## Source-bound observations

- 20 focused tests passed, including deliberate corrupt-label and boolean-grid
  rejection by the actual verifier using protected Racket.
- The two-demo audit passed 308 protected Racket applications: four episodes,
  every declared rival on every pair, and both settings on four size endpoints.
- The six-demo/four-query endpoint passed for both settings, with 32 additional
  protected Racket applications. Three-demo qualification is a separate receipt.
- All 24 sampled minimum-demo requests succeeded; the maximum observed search
  was 145 of the 256 allowed candidate attempts per band. This is a bounded
  Python sampler measurement, with reference execution measured separately.
- The 30×30 stress input contains 549 non-marker foreground cells, occupies all
  30 rows and columns, and has foreground in all four quadrants. It is a full
  symmetric field, not a padded 5×5 input.

An independent audit found that most-frequent-color and bbox-area selection
could fit both original demonstrations yet fail a query. Both original cases
were replayed in protected Racket, and both rivals now participate in teaching
selection. The repaired eight-seed audit (16 episodes, 96 pairs) found no
actionable ambiguity among its finite rivals. Evidence lives in
`WORK/checks/f283b8535697/`, including the retained before/after cases.

## Promotion and limits

The native contract is `promotion.json`; `evidence/manifest.json` binds the
prototype and focused test source. Native commands are:

```bash
python3 review.py run python3 -m arcpuzzles parametric manifest f283b8535697 --evidence generators/f283b8535697/workspace/parametric/evidence/current --include generators/f283b8535697/tests/test_parametric_symmetry.py --reported-checks '20 focused tests; finite protected-Racket rival/export/boundary audit; see WORK/checks/f283b8535697'
python3 review.py run python3 -m arcpuzzles parametric qualify f283b8535697 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/f283b8535697/qualification --summary
```

The existing manifest is guarded against replacement; rebuilding it requires
its exact prior hash via `--replace`. After integration the owner must qualify
and accept the exact live bytes. Reviewer evidence grants no native acceptance
or training admission.

Only finite rivals are checked. A 180-degree-only reconstruction is equivalent
on this lawful grammar and is not claimed to be refuted. Area with a secondary
cell-count tie-breaker and a modal minimum-color tie-breaker survived some
audited demonstrations without changing their queries; universal uniqueness is
not established. Inputs retain the original 5×5 occluder and even 10..30-side
envelope. Larger outputs would require a separate rule design.
