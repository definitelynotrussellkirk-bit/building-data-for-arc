# public_eval_3e6067c3: legend-ordered route family

Settings: `bridge_color=source|destination`. The canonical/default setting
uses the departing block's payload color and is byte-identical to
`../../reference.rkt`. The alternate uses the arriving block's color while
preserving the same occurrence-matched legend route and input grammar.

`generate(seed, settings, demos, queries)` accepts exact integer seeds,
2–6 demonstrations, and 1–4 query prefixes. Every episode retains a private
bank of exactly four distinct queries. `presentation_order(seed)` shuffles the
complete four-query bank independently; `public_view(episode, index)` emits one
visible query input with no answer, setting, program, future query, source index,
or total-count hint.

The sequential dependency is route decoding followed by corridor rendering:
read the detached singleton legend, occurrence-match repeated colors to framed
blocks in spatial reading order, then use that ordered route to choose which
aligned corridors to paint and which endpoint color supplies each corridor.

From the packet root, use fresh output directories:

```sh
python3 review.py run python3 -m pytest generators/public_eval_3e6067c3/tests -q
python3 review.py run python3 generators/public_eval_3e6067c3/workspace/parametric/audit.py \
  --out ../checks/public_eval_3e6067c3/audit --seeds 0 1 2 3 4 5 6 7 17 43 \
  --racket-seeds 0 17 43
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight \
  public_eval_3e6067c3 --root . --out ../checks/public_eval_3e6067c3/preflight
python3 review.py run python3 generators/public_eval_3e6067c3/workspace/parametric/audit.py \
  --out ../checks/public_eval_3e6067c3/causal \
  --causal-preflight ../checks/public_eval_3e6067c3/preflight/preflight.json
```

The finite rival audit is bounded evidence, not a proof of universal
identifiability or training value. Authoring preflight and reviewer causal replay
do not register, qualify, accept, or admit the family to training.
