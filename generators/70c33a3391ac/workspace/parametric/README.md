# Proposed episode-level occurrence-threshold parameter

This is a **task-local prototype**, not part of the selected canonical generator
or its approval path. It preserves the family’s core reasoning: find
four-connected nonzero components, crop each exact colored component, count
identical crops, and return the first crop in the canonical reversed scan order
that meets an episode-fixed occurrence threshold.

| parameter | allowed values | canonical/default |
|---|---|---|
| `minimum_occurrences` | `2`, `3` | `2` |

The default materializes the canonical Racket program byte-for-byte. The
alternative changes only its comparison from `count > 1` to `count > 2`.
Each retained scene contains one crop exactly twice, placed later in row-major
order, and a different crop exactly three times, placed earlier. Consequently
the canonical threshold returns the pair while threshold three returns the
triple. Two unique multicolor distractors remain. Every demonstration therefore
distinguishes both declared settings; the selected value is drawn once and
held fixed for the entire episode. Public challenge files omit the hidden
parameter, program, pair metadata, and query answers.

From the packet root:

```bash
python3 review.py run python3 \
  generators/70c33a3391ac/workspace/parametric/verify.py \
  --seed 20261021 \
  --out ../checks/parametric/report.json \
  --artifact-dir generators/70c33a3391ac/workspace/parametric/materialized
```

The verifier executes both exact Racket programs on every pair, checks them
against an independent Python mirror, retains complete private episodes and
masked public challenges, records source/program/runtime hashes, and saves one
lawful input where the settings disagree. This bounded evidence does not add a
production parametric API or approve the alternative rule.
