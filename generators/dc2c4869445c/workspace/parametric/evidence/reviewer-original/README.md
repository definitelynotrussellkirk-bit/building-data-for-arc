# Outward mirror gap — separate prototype

The single semantic parameter is **`gap ∈ {0, 1, 2}`**, original/default **0**.
Each nonzero 8-connected multicolor group still has a strict-plurality main
shape and one to three distinct singleton seed colors around one occupied bbox
corner. Each seed selects the same horizontal, vertical, or diagonal bbox-edge
mirror and the same paint color as the canonical task. After reflection, shift
that copy outward by `gap` cells on **each indicated axis**. Retain the entire
input, including the original seed cue cells; do not move or erase those cues.
Consequently the gap describes copy displacement, not a promise of a wholly
empty strip where cue cells sit.

`gap=0` emits the exact canonical Racket text. For alternatives, four checked
coordinate expressions gain signed outward translations; changed source forms
fail explicitly. `RuleExecutor` uses the shared `strip_rule_wrapper` parser and
the real `RacketBridge` on the self-contained native lambda. It does not require
the absent legacy `scripts` import used by the generic source normalizer.

## Run from the outer packet directory

With the packet's isolated review interpreter:

```bash
WORK/.venv-review/bin/python review.py run ../.venv-review/bin/python \
  generators/dc2c4869445c/workspace/parametric/gap_variant.py \
  --gap all --seed 1729 --train 3 --test 1 --max-attempts 256 \
  --out ../checks/parametric/gap-all-1729

WORK/.venv-review/bin/python review.py run ../.venv-review/bin/python -m pytest \
  generators/dc2c4869445c/tests/test_parametric_dc2c4869445c.py -q
```

If the default interpreter already has the packet dependencies, replace both
interpreter paths with `python3`. Output directories must be new. `--gap 0`
(the default), `1`, or `2` emits one episode. `--gap seed --episode-index N`
selects one gap from a stable hash of the seed and episode index **once**, then
uses it for every demonstration and query. `--gap all` deliberately uses the
same four accepted inputs for three controlled comparison episodes.
The `--gap all` ordinal filenames reveal the enumeration order (0, 1, 2).
That bundle is a controlled comparison, **not a blinded evaluation challenge**;
its public JSON still contains only the specified grids.

The original generator draws each candidate at exactly `(seed, sample_index,
difficulty)` with no layout overrides. The sampler accepts only candidates that
pass the canonical structural check and whose copies at **all three settings**
stay in bounds, preserve every input cell, and avoid distinct seed/group target
overlap. Painting a seed's own cue in the same color is permitted. Rejected
indices and reasons are retained. Sampling has an explicit attempt cap (1..4096)
and raises `SamplingError` if incomplete; it never returns a shortened episode.
Demo count is 3..20, query count 1..10, total pair count at most 30.

## Evidence and public boundary

The command verifies gap 0 on **all canonical pairs** and executes every accepted
input under all three exact Racket programs. The Python mirror is only a parity
check. Every episode must eliminate both rival parameter values using its
demonstrations, before querying; ambiguity fails loudly. No other semantic rival
family is claimed to be exhausted. With one query it also measures every
single-pair query holdout using the already executed labels: four rotations,
with both parameter rivals checked in each, for the default 3-demo/1-query case.
Multiple-query episodes explicitly report that holdout analysis was not run.

- `public/episode-NNN.json`: **only** train input/output and test input. No seed,
  hidden parameter, reference program, hashes, or query output.
- `private/episode-NNN.json`: hidden fixed gap, full labels, per-pair hashes,
  sample indices, and actual-Racket rival predictions' hashes/mismatch indices.
- `programs/gap-N.rkt`: exact raw `(rule! ...)` source. The sibling
  `gap-N.callable.rkt` holds the stripped native lambda and `gap-N.definition.rkt`
  holds the exact definition argument passed to `RacketBridge.eval_text`.
  Each has its own SHA-256 in `report.json`; these are deliberately distinct
  identities. The bridge performs its usual transport whitespace normalization.
- `cross-setting-witness.json`: one common input and all three different outputs.
- `sampling.json`: deterministic seed/index provenance, accepted pairs and all
  rejections; `canonical-parity.json`: every canonical record's equality result.
- `report.json`: settings, source/artifact hashes, runtime identity, actual payload
  argv, counts, and limitations. Source hashes bind the actual imported helper
  files in either the library or staged execution layout. Failures instead
  retain `failure.json` with the request and pre-execution source identities
  (when available), emitted program identities, and the original error, then
  exit 1. No completed report is written for an incomplete run.

This is a **proposed authoring prototype**. It does not change the selected
generator, canonical rule, runtime API, approval pins, or training admission.
The focused tests cover asymmetric coordinate semantics in every corner,
diagonal connectivity, cue preservation, invalid gap values, clipping and
collision filtering, all canonical records, deterministic replay, fixed episode
semantics, rival elimination, incomplete sampling, and the public data boundary.
The writer regression exercises real Racket, serialized public/private files,
runtime identity, artifact hashes, and the source-bound failure path.
Finite evidence at the reported seed does not establish all-seed support or a
production distribution. New runs hash the then-current selected source; rerun
after source changes before citing a receipt as current.
