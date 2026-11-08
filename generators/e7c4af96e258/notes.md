# Working notes: e7c4af96e258


## 2026-10-26 second adversarial pass

A wider lesson audit found that the original two demonstrations distinguished the
two declared settings but did not always eliminate cheap positional and alternate-
distance rules. For example, topmost, rightmost, lexicographic, Manhattan,
centroid, and bbox-origin selectors could fit both demos on some seeds and then
disagree on a query. The repaired sampler now searches deterministic alternative
training streams and chooses the first pair whose demonstration-only finite
certificate leaves exactly the selected policy. The certificate is retained in
each episode and checked by the bounded probe.

The same pass found a structural verifier hole: a connected symmetric four-cell
yellow impostor could satisfy the old source/target count checks. Generator v3.1.0
now requires exactly four nearby source markers, 4-connectivity, eight distinct D4
images, D4-equivalent four-cell target components, and one-to-one correspondence
between yellow components and lawful stamp footprints. The footprint cache used
by teaching audits is capped at 256 entries.

## 2026-10-26 review result

Repaired the base and built a complete authoring-stage native parametric proposal. This is **not** owner acceptance and does not admit training data.

### Base repair

The inherited generator advertised several inert controls, silently accepted unknown keys, ignored exact `grid_h`/`grid_w`/`marker_count` requests, and accepted color-count impostors. Version 3.1.0 narrows the declared surface to four observable axes:

- `grid_h=13..20`
- `grid_w=15..22`
- `marker_count=1..3`
- `texture=standard`

Every explicit legal value is now honored independently of difficulty; unknown names, booleans/coercions, invalid difficulty, and out-of-range values reject. Generated yellow marker constellations are connected four-cell chiral shapes with eight distinct D4 images. `self_check()` now reconstructs the source marker relation and requires a real non-source D4 stamp site. `observe_overrides()` recovers dimensions, semantic target count, and texture from the returned grid.

### Parametric family

`target_policy` has two settings:

- `all_matches`: byte-exact canonical Racket source; enumerate every matching D4 footprint and stamp all of them.
- `farthest_match`: use the same candidate enumeration, remove the source footprint, score each remaining candidate by summed squared distance from the source bbox origin, then stamp only the maximum-score footprint.

The sampler is hidden-setting independent, always constructs two non-source candidates with unequal scores, supports 2–6 demonstrations and 1–4 independent queries, and uses query shapes `13x15`, `17x20`, `24x26`, and `30x30`.

### Sequential dependency

- **A:** enumerate complete D4 marker matches.
- **Intermediate:** non-source candidate red footprints plus their input-dependent squared-distance scores.
- **B:** select the maximum-score candidate and stamp only it.

B cannot choose a location before A reveals which candidate footprints exist. `nearest.rkt` changes only B to choose the minimum-score non-source candidate. The protected witness replays two cases, including a 30x30 case, and proves the final outputs differ.

### Strongest cheap shortcuts tested

The retained finite rival family now covers nearest, first/last, four edge-position selectors, and three alternate distance functionals in addition to both declared settings. The first two demonstrations are selected jointly until every wrong named selector is rejected by at least one visible example. The bounded probe rechecks the certificate and still verifies the nearest-stage causal counterfactual on all 18 sampled pairs. The wider deterministic audit covered 288 lessons (both settings for seeds 0..143) and 240 supported count-prefix requests without a surviving declared shortcut.

### Executed evidence

- 26 focused pytest checks passed.
- Exhaustive declared-axis boundary audit: 2,304 legal combinations passed across three seeds and four difficulty bands; the symmetric-marker regression was rejected.
- 18-case sampler/shortcut probe passed and independently recomputed each finite teaching certificate.
- Wider teaching audit: 288 lessons over seeds 0..143 plus 240 all-count prefix requests passed.
- Protected native worker: 6 jobs, 48 Racket evaluations, sole setting survivor from two demos.
- Authoring base preflight: 4 original canonical pairs, 2 ordinary generator draws, 24 parametric labeled pairs, 32 protected Racket evaluations.
- Protected sequential witness: 2 cases, farthest vs nearest counterfactual.
- Public projection: 4 episodes / 16 one-query views; projection verification passed.
- First-turn privacy/count-independence: 4 first turns, 24 invariance checks, no failures.

Primary receipts are under `checks/e7c4af96e258/`; source inventory is `workspace/parametric/evidence/manifest.json`.

### Limits

The finite two-setting qualification does not prove uniqueness against every possible rule. The authored distance functional is part of the alternative setting, not canonical semantics. Owner source review, native qualification after integration, and explicit acceptance are still required.
