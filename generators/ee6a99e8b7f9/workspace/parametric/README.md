# Proposed `pink_center_tie` prototype

This task-local prototype preserves the original rectangle/dot reasoning and
varies one hidden rule choice once per episode:

- `lower` — canonical/default: use the lower-indexed center cell on an even
  pink axis (`floor((lo + hi) / 2)`).
- `upper` — proposed: use the upper-indexed center cell
  (`ceil((lo + hi) / 2)`).

Gray behavior, pink source clearing, object detection, and odd-axis behavior are
unchanged. Each retained episode has three demonstrations and one query; every
pair contains an even-axis pink witness and distinguishes both settings. The
public challenge omits the hidden setting, Racket source, and query answer.

Run from `WORK/repo` through the packet's Racket-enabled wrapper:

```bash
python3 ../../review.py run python3 \
  generators/ee6a99e8b7f9/workspace/parametric/prototype.py \
  materialize --out ../checks/parametric/pink-center-tie-v1
```

For a copy beside the prototype, omit `--out`. Exact Racket programs, complete
private episodes, redacted public challenges, hashes, rival disagreement counts,
and limitations are written to the output directory. This is a proposed
prototype only; it does not modify or approve the selected production rule.
