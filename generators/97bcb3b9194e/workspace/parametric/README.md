# Selection-mode prototype (proposed, not canonical)

This task-local prototype varies one hidden rule parameter once per complete
3-demonstration/1-query episode while retaining the selected production input
sampler:

| Parameter | Allowed values | Canonical/default |
| --- | --- | --- |
| `selection_mode` | `fewest`, `most` non-blue marks | `fewest` |

Both settings preserve the original reasoning structure: find separated filled
rectangles, count every mark whose color is neither background `0` nor body
blue `1`, select a count extremum, and return that rectangle unchanged. The
`fewest` setting is the exact canonical Racket program. The `most` setting
changes only the strict comparator in the mark-count sort. Every retained input
contains at least two marked rectangles, so the selected minimum and maximum
outputs differ even when the maximum itself is tied; canonical stable row-major
tie behavior is retained.

The script executes both exact Racket programs through the included bridge,
checks them against an independent Python mirror, and writes separate public and
private evidence. Public challenges omit the hidden setting, Racket source, and
query answer. This prototype does not change or approve the selected canonical
rule.

From the outer extraction directory run:

```bash
python3 review.py run python3 \
  generators/97bcb3b9194e/workspace/parametric/prototype.py \
  --seeds 0 1 2 3 --difficulty easy \
  --out-dir ../checks/parametric/selection-mode-v2
```

The command fails unless the retained seeds cover both settings, both Racket
programs agree with the independent Python mirror, and all demonstrations plus
the query distinguish `fewest` from `most`.
