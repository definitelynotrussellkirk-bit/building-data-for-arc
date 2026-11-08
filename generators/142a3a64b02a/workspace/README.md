# Workspace for 142a3a64b02a

`semantic_audit.py` is the retained task-local probe for the whole-component curriculum boundary. It materializes consecutive `EXAMPLES_NEEDED + 1` windows from the production sampler, rotates every pair into the query position, and evaluates the generator's actual `LESSON_COMPETITORS` plus the `lesson_identifiable` hook.

Run the final review sweep from the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/142a3a64b02a/workspace/semantic_audit.py \
  --seeds 32 --starts 6 \
  --out ../checks/semantic-audit-final.json
```

The default range covers all three difficulty bands, seeds `0..31`, and schedule starts `0..5`. Exit status is nonzero if any generated pair is invalid, a declared rival fits every demonstration and disagrees on the held-out query, or the direct calculation disagrees with `lesson_identifiable`.

The probe uses the independent Python rule mirror for labels. It is not a substitute for the Racket rule smoke/authority checks or `arcpuzzles lesson-census`; its value is inexpensive exhaustive rotation across a small deterministic schedule.
