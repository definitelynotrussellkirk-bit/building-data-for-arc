# Completion-count route family

This task-local native adapter preserves the selected canonical rule as the exact
default and adds one nearby episode-fixed alternative.

| `finish_rule` | behavior |
|---|---|
| `complete_only` | Exact selected canonical Racket source, byte-for-byte: inspect the original grid's 2x2 windows, simultaneously fill the missing corner of each three-equal-nonzero L, and preserve all other cells. |
| `route_dominant` | First perform the same canonical completions. Count the newly completed cells by color, select the unique color with the largest completion count, then connect its newly completed cells whenever they share a row or column. |

## Required sequential dependency

- **A:** discover every qualifying local 2x2 completion in the original input and
  apply those fills simultaneously.
- **Intermediate:** the completed grid, the newly completed coordinates grouped
  by color, their per-color counts, and the unique count-winning color.
- **B:** on the completed grid, route only the winning color between aligned
  newly completed coordinates.
- **Why B depends on A:** the route endpoints and selected color are properties
  of A's newly generated target set, not of the raw color frequencies. The
  retained counterfactual chooses the raw-input-most color instead; protected
  Racket execution changes the final output.

Inputs are matched across settings. Every sampled scene has completion counts
3/2/1, while a large solid rectangle makes the raw-input-most color differ from
the completion-count winner. The three winning targets form both a horizontal
and a vertical relation. The runner-up has aligned targets but must not route.
This construction makes the visible demonstrations distinguish the two declared
settings and several natural shortcut rules.

The adapter supports 2--6 demonstrations and 1--4 independent queries. Query
prefixes are stable; a four-query episode includes an exact 30x30 scene with
substantive content in all four quadrants and contact with all four boundaries.
Public projection exposes only demonstrations and the current query input. It
omits settings, Racket source, answers, future queries, and total-query hints.

From the packet's outer directory:

```bash
python3 review.py run python3 -m pytest \
  generators/6d678fbbe87e/tests/test_native_parametric.py -q
python3 review.py run python3 \
  generators/6d678fbbe87e/workspace/parametric/audit.py \
  --out generators/6d678fbbe87e/workspace/parametric/evidence/current
python3 review.py run python3 -m arcpuzzles parametric qualify 6d678fbbe87e \
  --out ../checks/6d678fbbe87e/qualification --summary
```

The retained audit is finite. It verifies the declared settings on seeds 0 and
17, four queries, minimum/maximum supported canvases, public/private projection,
and nine executable rivals through protected Racket. It is not a proof of unique
induction against every possible rule. This prototype is reviewer-ready only
after the packet's native qualification; owner acceptance and training admission
remain separate downstream decisions.
