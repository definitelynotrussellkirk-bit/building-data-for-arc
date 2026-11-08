# Area or perimeter ranking

This opt-in family keeps the source task's legend and cardinal-component reasoning.
The episode-fixed private parameter is `rank_by: area | perimeter`. Components
are ordered by descending measurement, then their top bounding row and left
bounding column. The legend assigns colors in that order; row zero is preserved.
Perimeter counts exposed cardinal cell edges, including boundaries around holes.
If all three sorting keys coincide, the Python labeler preserves the canonical
Racket program's reverse-discovery stable order. The sampler avoids such complete
ties; a literal regression checks this additional admitted-grammar case in both
settings through protected Racket.

`area.rkt` is byte-for-byte the canonical program. The production generator,
canonical authority, and production approval are unchanged. `perimeter.rkt` adds
an input-dependent measurement consumed by the ranking step. Replacing those
measurements with areas changes the output on the first teaching example; the
return's native causal witness executes and replays that counterfactual.

## Contract and lessons

- Native entry points: `adapter.program(settings)` and
  `adapter.generate(seed, settings, demos, queries)`; exact integer seed
  `0..2**63-1`, independent `demos=2..6`, `queries=1..4`.
- Use three demonstrations and four controller-side queries ordinarily. Two
  constructive demonstrations already reject the twelve declared hypotheses.
  Extra demonstrations vary shape, size and placement without changing the rule.
- Inputs match between settings. Separate seed/split/index streams make the first
  query and visible demonstrations independent of the requested future queries.
- Body components use color 8; the legend has distinct nonzero colors and may
  itself contain 8. The first demonstration places 8 within the legend so rules
  that force it to either end fail. Shapes may meet diagonally without merging.
- The second demonstration includes equal-measure ties, a ring, a solid square,
  and a bar. It distinguishes counting occupied cells from filling holes, and
  full boundary length from bounding-box or exterior-only perimeter.
- Queries are 16×19/5 components, 22×25/6, 30×30/8, and 24×30/7. The larger
  scenes fill separated slots with solid, frame, comb, elbow and notched shapes;
  this is a separate distribution extension beyond the compact production sampler.
- The solver grammar accepts 5..30 by 5..30 rectangular integer-color grids,
  with 2..8 cardinal components and an equal-length contiguous legend. Emitted
  demonstration/query profiles occupy the dimensions above and 12×16 through
  17×21 for demonstrations. A literal 5×5 boundary case is Racket-checked.

## Reusable audit

From the issued review directory, using its configured Python/Racket launcher:

```bash
python3 review.py run python3 \
  generators/41a5c2fcf25a/workspace/parametric/audit.py \
  --out ../checks/41a5c2fcf25a/new-audit
```

Use a new output directory. The audit runs 24 episodes: both settings, seeds
0, 17, 29 and the maximum seed, and demo counts 2, 3 and 6 with four queries.
It records every rival's demonstration mismatches separately from query
disagreements. The twelve Python hypotheses are the other measurement,
position-only order, ascending order, sorted legend, reversed ties, column-first
ties, source color first or last, capped measurement, eight-neighbor components,
bounding-box measurement, and filled-hole measurement. No rival survived the
demonstrations in the retained bounded audit. This is not universal uniqueness.

The audit also runs both declared programs through protected Racket at demo-count
endpoints on seed 29: 48 evaluations plus four literal evaluations (5×5 and
complete-key ties in both settings). It checks
matched inputs, first-turn equivalence, private-metadata invariance, and content
coverage. The isolated task suite has 65 passing tests, including an independent
lattice-edge cancellation oracle for perimeter. Native qualification separately
checks seeds 0 and 17 at three demos and four queries.

## Public and private examples

`evidence/verified/public/` contains two hash-named, four-query **controller**
challenges, one for each setting. An actor receives just one file from
`public_turns/` per user turn. `adapter.public_turn(episode, query_index)` uses
the same projection and includes no future query, total-count hint, setting,
program, or query answer. The first turn equals a single-query request.
Public IDs come only from the existing public-byte serialization helper.

`private.json` maps controller IDs to ordered turn IDs, settings, programs,
answers and teaching checks. `execution.json` contains the protected audit
execution. Keep these private. The runtime worker's generic reference string
does not grant acceptance; the examples explicitly record owner acceptance as
pending and training admission as false.

The native `evidence/manifest.json` inventories exact source and evidence bytes.
This return is a qualified reviewer proposal. The owner must qualify and accept
the integrated exact bytes before using the accepted-family export API. The
recorded capped-area and diagonal-connectivity findings on the unchanged
production sampler remain open; the new family's demonstrations address those
contrasts without claiming to repair or reapprove production sampling.
