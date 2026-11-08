# Working notes: ec1260207f71

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current proposed row-transfer family

`workspace/parametric/` now contains a native adapter, bounded promotion contract,
exact canonical Racket resource, sampler, teaching verifier, public exporter and
protected-Racket replay command. The episode-fixed parameter is
`transfer_order=aligned|reversed`: retain the marker's offset at the plain bar,
or map it to `bar_length - 1 - offset`. Joining and recoloring the original
marker are unchanged. The aligned program is exactly the selected canonical text.

The prototype supports 2–6 demonstrations and 1–4 queries independently, with
ordinary requests of 3 and 4. The first two demos cover both side and row-band
branches, and asymmetric offsets identify the parameter. Inputs match across
settings for paired seeds. Four distinct query profiles range from 14×7 to
30×30; the maximum uses two 14-cell bars and 12 markers with boundary contacts.
This extension is separate from the production sampler's 28×16 maximum.

The teaching contract is limited to the two settings and seven named executable
shortcuts; it does not exclude arbitrary conjunctive alternatives. Public IDs
hash only visible bytes. `visible_turn` exposes one query without future inputs
or count hints and preserves exact single-query first-turn equivalence.
See `workspace/parametric/README.md` for reproducible commands and sampling limits;
the source-bound current verification receipt is in its `evidence/current/`.

The existing canonical `upper_only` lesson finding, absent semantic contract,
and authority-text divergence in `evidence/review_index.json` remain unresolved.
The production generator and reference authority are unchanged; the prototype's
constructive demonstrations do not retroactively clear the canonical audit.
Next step: owner review, native qualification and exact-source acceptance of
this proposed family, with any production teaching/authority repair handled as
its own source-bound change. No training admission is implied.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/ec1260207f71/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
