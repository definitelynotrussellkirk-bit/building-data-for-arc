# Review — 22d1f016cb3d boundary-palette prototype

Task/source: `22d1f016cb3d`; production generator SHA-256 remains `26f3491ab54d2e4cd38590da33f59a567f140c2e8a342a1dcfd5ab59f701abbd`.
Prototype: `workspace/parametric/prototype.py` upgraded from `1.0.0` to `1.1.0`.
Defect → repair: fixed 4-demo/1-query slicing became independently validated demo/query counts over ten distinct scheduled pairs.
Defect → repair: setting-bearing public filenames became exact visible-content SHA-256 IDs via the shared public projection helpers.
Checks: focused prototype suite **23/23 passed**; all selected-task tests **68/68 passed**.
Racket evidence: **16/16 executed pairs** across two fixed settings, with four demonstrations and four distinct queries per setting; Python/Racket labels match.
Teaching evidence: every retained demonstration refutes the opposite palette and every retained query changes under it.
Privacy/writer evidence: hidden settings, seeds, programs, query answers, and private iteration order do not affect public IDs; writes are sorted and duplicate-safe.
Final invariant replay: source hashes, 16 executed pairs, Racket identities, exact public bytes, sorted IDs, and clean public inventory all passed the retained verifier.
Reference rule changes: none; canonical hash remains `2219db85ca5f`, and both retained Racket files are byte-exact to their materialized settings.
Production scope: unchanged; no production battery was rerun for this prototype-only patch.
Disposition: **routine prototype follow-up complete; not production approval or training admission**.

## Built artifacts

The prototype now accepts `demo_count` and `query_count` separately, rejects non-literal/nonpositive/over-capacity values, and retains the historical Python default of 4 demonstrations plus 1 query. The evidence/CLI default is 4+4. The public writer plans the whole batch before creating its destination, rejects duplicate visible payloads, sorts by public ID, and writes the exact bytes hashed by `reviewer_support.public_challenge_id`.

Current visible-content exports:

- `challenge-18bf52a2d1943b0a221245b10dc7df9b84088dd66219b1e5bc4e47adbb71bbaf.json`
- `challenge-ad98108e4c2bca9dabca31c66b7d192a0b20e0edcea93eccb4aaa274f375c864.json`

The older `ends*_public.json` fixtures remain unchanged historical baseline artifacts; version 1.1.0 does not emit them.

## Supplementary tickets

`ticket-0ba197bd2b14a510` completed one source-bound API comparison for `3108da8bf9e8`: valid `omitted_count=0` is realized and observed exactly, while boolean `True` is rejected with `TypeError`. This is not a universal peer audit and produced no safety finding.

`ticket-a42cea8093566f13` deterministically sampled `8b6a2892a064`, `022556f7ee2c`, and `a178821cc6bf`. All three catalog rows have dataset `mix_weight=1.0`, but retained quality differs sharply: one has a reproduced unresolved three-demo teaching shortcut, one is independently checked with strong semantic hooks, and one has weaker current receipt continuity. The proposal preserves the 10% evaluation focus and every existing draw/approval/training boundary while testing a four-intervention post-draw evidence-gap queue.

## Remaining limits

Evidence is finite to the two declared palette settings, seeds 18/19, ten scheduled source rows, and the opposite-palette rival. Four distinct generated queries are not a claim against undeclared rules. No full production battery, corpus-wide deduplication, model evaluation, or source-family ranking was run. The allocation sample contained no ARC-GEN or RE-ARC record, so it supports no comparative conclusion about either source.
