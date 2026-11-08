# a44e3443619f parametric cascade prototype

This proposed family keeps the selected canonical program byte-for-byte as
`completion_depth=single`.  `completion_depth=cascade` executes that pass, then
recolours a red cell green when the newly blue intermediate supplies all four
of its diagonal neighbours.  The hidden setting never changes input sampling.

The minimum two-demo lesson contains a complete cascade, an eight-red-cell
near miss, a standalone X and a partial X across the pair.  Every episode has
four distinct queries; the last is a substantive 30×30 boundary-contact scene.

From the packet root:

```sh
python3 review.py run python3 -m pytest \
  generators/a44e3443619f/tests/test_parametric_cascade.py -q
python3 review.py run python3 \
  generators/a44e3443619f/workspace/parametric/adversarial_audit.py \
  --out generators/a44e3443619f/workspace/parametric/evidence/adversarial-audit.json
python3 review.py run python3 -m arcpuzzles parametric manifest a44e3443619f \
  --evidence generators/a44e3443619f/workspace/parametric/evidence \
  --reported-checks 'focused pytest plus protected-Racket adversarial audit'
python3 review.py run python3 -m arcpuzzles.review_base_preflight a44e3443619f \
  --out ../checks/a44e3443619f/qualification
```

These are reviewer authoring checks.  The owner must review the exact source,
rerun native qualification/acceptance, and separately decide training admission.
