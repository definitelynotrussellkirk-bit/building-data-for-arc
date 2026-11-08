# Parametric orbit-completion family

This task-local family preserves the selected canonical program byte-for-byte as
`completion_scope=all_orbits`.  The alternate setting,
`completion_scope=most_clipped`, first computes every blue source marker's
in-bounds quarter-turn orbit around the unique red pivot, selects the unique
orbit with the fewest visible members, and completes only that orbit.

The input sampler is independent of the private setting.  It supports 2–6
demonstrations and 1–4 queries, while qualification and authoring examples use
four private queries.  The fourth query is a constructive 30×30 stress case with
a unique count-2 target, count-3 and complete-orbit distractors, all four edge
bands and all four quadrants represented.  Public projection reveals all
labelled demonstrations and exactly one current query input; settings, programs,
answers, future queries and total-count hints remain private.

The finite teaching audit checks the other setting and eight additional
executable shortcuts: least-clipped, first/last marker, nearest/farthest pivot,
complete-only, clipped-only and first-partial.  This is bounded evidence, not a
proof of unique induction over all possible programs.

Run the reusable protected-Racket audit through the packet launcher:

```bash
python3 review.py run python3 \
  generators/ba0c6a5828f9/workspace/parametric/audit.py build \
  --out ../checks/ba0c6a5828f9/authoring-audit
python3 review.py run python3 \
  generators/ba0c6a5828f9/workspace/parametric/audit.py verify \
  --out ../checks/ba0c6a5828f9/authoring-audit
```

The required causal chain is:

1. **A:** enumerate each source marker's four rotations and retain only its
   input-dependent in-bounds orbit members and visible count;
2. **intermediate:** the unique source marker/orbit with the minimum visible
   count;
3. **B:** paint the selected orbit only.

A wrong-intermediate witness substitutes the least-clipped (maximum visible
count) orbit.  On the retained case that changes the protected-Racket output.
Owner acceptance and training admission remain separate downstream decisions.
