# Expansion-mode parametric prototype

This task-local prototype proposes one episode-level hidden parameter:

- `bbox` (canonical/default): repaint the full bounding box formed by the framed rectangle and cyan marker.
- `corridor`: preserve the framed rectangle and draw only a frame-color one-cell-wide corridor to the marker.

The mode is sampled **once per episode**. All three demonstrations and the one query use that same mode. Inputs are sampled from a separate deterministic stream, so the hidden mode cannot alter the input distribution. The public challenge contains only three labeled pairs and one unlabeled query; parameter values and Racket programs remain in private evidence.

The executable evidence runs both exact Racket programs on both retained episodes, cross-checks every output with an independent Python mirror, and rotates each of the four pairs through the query position. Every alternate-mode rival must be refuted by the remaining three demonstrations.

This is a bounded proposal only. It does not modify the canonical rule, production generator API, catalog, or approval state.

From the packet root:

```bash
python3 review.py run python3 generators/a3c33cc348fb/workspace/parametric/prototype.py \
  --base-seed 20261022 \
  --out ../checks/parametric/expansion-mode-v1
```
