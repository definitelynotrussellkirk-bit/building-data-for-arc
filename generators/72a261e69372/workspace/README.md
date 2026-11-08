# Workspace

The selected implementation is `../generator.py`. Workspace files are analysis tools and are never selected automatically.

## `reference_probe.py`

Independent task-local oracle and census tool. It deliberately does not call the generator's private rule-mirror helpers.

From the packet root, with the bundled Racket runtime prepared:

```bash
python3 run_with_racket.py python3 generators/72a261e69372/workspace/reference_probe.py \
  --per-band 200 \
  --out ../checks/72a261e69372-independent-audit-final.json \
  --racket
```

The probe:

- checks canonical pairs with an independent Python implementation;
- samples 200 pinned generated inputs in each difficulty band;
- records determinism, validation, output change, axis support, canonical profiles, and disagreements with every declared rival;
- reconstructs the actual four-demo lesson schedule for 200 seeds per band and calls `lesson_identifiable`;
- checks 99 balanced canonical/generated inputs against the selected real Racket rule when `--racket` is supplied.

The report is bounded evidence, not a universal induction claim. Keep failed command logs and use the successful JSON's source hashes when citing results.
