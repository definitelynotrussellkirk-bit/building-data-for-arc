# Public `a32d8b75` sidebar-stamp family

Private episode setting:

- `scope=all` — exact canonical rule; stamp the complete glyph.
- `scope=texture_indexed_component` — count the swapped texture's top-left
  color, select `(count - 1) mod n` among row-major four-connected glyph
  components, then rotate and stamp only that selected component.

The adapter supports 2–6 demonstrations and 1–4 queries.  It always constructs
the complete deterministic ten-input bank first, so demo/query prefixes are
stable and both settings receive byte-identical inputs.  Four query profiles are
stored; one is a substantive 30×30 input.  Use `presentation_order(seed)` to
shuffle all four source queries privately and `public_view(episode, index)` to
emit a single visible query without its answer or future queries.

From the packet outer directory:

```bash
python3 review.py run --receipt checks/public_eval_a32d8b75-tests/task-local-final.json \
  python3 -m pytest -q generators/public_eval_a32d8b75/tests/test_public_family.py

python3 review.py run python3 -m arcpuzzles.review_public_creation preflight \
  public_eval_a32d8b75 --root . --out ../checks/public_eval_a32d8b75/preflight

python3 review.py run python3 ../checks/tools/audit_public_families.py \
  --root . --checks ../checks
python3 review.py run python3 ../checks/tools/build_public_witnesses.py \
  --root . --checks ../checks
```

The preflight executes all supplied official labels and both setting programs in
protected Racket, but is explicitly not owner qualification or acceptance.
`checks/public_eval_a32d8b75/causal/witness.json` binds the selected-component
intermediate to the exact preflight source and replays an off-by-one selector
counterfactual.  The adversarial audit is finite and does not prove universal
identifiability.
