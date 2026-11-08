# Working notes: 20d2c3da584a

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.


## Current canonical-interior coverage finding

Reviewer-reported static AST exhaustion: four generated templates have boundingboxes3x2,3x2,2x3,2x3,so nonecontainsastrictinterior; borderpaint equalswholeboxfill throughoutthisgrammar. Currentcanonicaltrain[1](5,4)andtrain[3](8,4) distinguishwholeboxrival fromborder. NoRacket/batteryrun,wronggeneratedlabelorfrequencyclaim. Addlawfulhollowinteriorwitness/rival and exactRacketlabelinaseparatecandidate. AuditedsourceSHA256 `014464ab3ad440e84abae9d2e79ed598e78f81a133be574274f2a62be7a1e798`; unresolved source-boundevidence: `generators/20d2c3da584a/counterexamples/allocation-c91c8b8b50062268/audit_assets.json`.
