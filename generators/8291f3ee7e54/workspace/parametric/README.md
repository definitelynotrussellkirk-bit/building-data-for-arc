# Native ring-order parameter family

Status: **reviewer-ready native adapter; exact-source owner acceptance pending**.
The production generator and canonical Racket authority are unchanged. Native
qualification is finite evidence only; `training_admitted` remains `false`.

## Contract

The episode-fixed parameter is `ring_order`:

- `largest_outside` — exact canonical/default program. Select each color's
  largest-span 4-connected component, sort selected spans descending, and paint
  each selected color on its matching centered ring.
- `smallest_outside` — preserve those same input-dependent ring geometries, but
  reverse the span-ranked color sequence before assigning colors outside-in.

`promotion.json` exposes 2–6 demonstrations and 1–4 queries. Inputs are
independent of the hidden setting. Ten deterministic slots are constructed before
count slicing: six demonstration slots followed by four query slots. Therefore
the first query is unchanged between one-query and four-query requests.

The first query is a real 30×30 five-component extension with selected spans
`[11, 9, 7, 5, 3]`, boundary contacts on every side, and a detached singleton of
the largest color. It exercises the same component/span rule rather than padding
a smaller puzzle, and it makes the easier union-bbox shortcut visibly wrong.

## Public and private data

Public challenges contain only labeled demonstrations and query inputs. Hidden
settings, seeds, Racket programs, rival outputs, and query answers remain private.
Visible IDs hash the exact public bytes. The retained prototype writer validates
the whole batch before publishing any episode, rejects duplicate visible IDs,
and writes both report rows and physical public files in sorted visible-ID order.

## Sequential dependency

1. **A:** select the largest-span connected component per color and sort the
   resulting layer records by selected span.
2. **Intermediate:** the input-dependent ordered list of colors, selected boxes,
   and spans.
3. **B:** use those spans to choose output size and ring offsets, then assign the
   ordered colors according to `ring_order`.

B cannot determine the final grid without A. The retained protected-Racket
witness substitutes disconnected same-color union boxes for A's selected boxes;
that wrong intermediate changes the final output for both qualified settings.

## Checks retained in this return

- 48 focused parametric tests pass.
- Full selected-task tests: 57 passed, 9 subtests passed; one pre-existing
  `GenCtx._draw_bounds` deprecation warning remains.
- Bounded shortcut audit: 60 protected-Racket evaluations across both settings
  and four named rivals; all rivals are refuted by demonstrations and differ on
  queries.
- Native qualification: settings × seeds `{0,17}`, three demonstrations and four
  queries per job, 40 protected-Racket evaluations, exact canonical default.
- Sequential witness: two protected-Racket wrong-intermediate cases replayed.

From the outer packet directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/8291f3ee7e54/tests/test_parametric_native_adapter.py \
  generators/8291f3ee7e54/tests/test_parametric_ring_order.py

python3 review.py run python3 \
  generators/8291f3ee7e54/workspace/parametric/audit_native.py \
  --seed 0 --out ../checks/8291f3ee7e54/self-audit.json

python3 review.py run python3 -m arcpuzzles parametric qualify 8291f3ee7e54 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/8291f3ee7e54/qualification --summary
```

The owner must integrate these exact bytes, replay qualification and the causal
witness on the live tree, and explicitly accept the family before use.
