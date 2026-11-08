# Working notes: 4cea2727fcf9

## Final design

- Preserved the exact canonical Racket default (`fbb3bae580b8bd2c900b133fd211e8cfd4ce40a8dcc3a1e83ccf8823fea3a9d3`).
- Repaired the base color-role description and bound `RULE_HASH = "fbb3bae580b8"`.
- Replaced decorative palette/count axes with the three controls actually consumed by ordinary generation: `grid_h`, `grid_w`, and `n_walls`.
- Scheduled portal-absent/present examples by sample-index parity. Every portal-present ordinary draw is rejected unless removing teleportation changes the label; every draw also requires the checkpoint to change the label.
- Chose one episode-fixed parameter, `portal_phase`: `always` (canonical), `before_checkpoint`, or `after_checkpoint`. This preserves the route/search reasoning while making checkpoint state control whether portals are active.
- Used constructive crossed controls instead of hoping random examples identify the setting: the first demo distinguishes pre-checkpoint portal use and the second distinguishes post-checkpoint portal use. Two demos are sufficient; 2–6 are supported without changing the four queries.
- Queries are deterministic, distinct, and matched across settings. The fourth is a substantive 30×30 case with distributed walls and boundary contacts.

## Adversarial findings and repairs

- Prior retained failure: a portal could be visible in all demonstrations while an ignore-portals rule still fit them. The new teaching profiles require a portal-caused output difference.
- Prior retained failure: declared palette/texture controls were ignored. They were removed rather than simulated.
- First strict audit after the repair warned that three presence-only entries were advertised as semantic witnesses. Added a regression and kept only the two causal witnesses with executable rivals (`ignore_portals`, `ignore_checkpoint`). Presence/absence coverage remains in the focused lesson tests.
- Bounded attack covered wrong portal phase, ignoring portals, skipping checkpoint state, identity, painting every walkable cell, deterministic replay, count corners, 30×30 substance, and first-turn leakage. No tested shortcut survived 12 protected-Racket episodes.

## Evidence and limits

- Generator SHA-256: `8dbaaa454153ac75eba6a7570afca498879b703d67896fbe3480283693bb698a`.
- Authoring qualification SHA-256: `a91c2b8815a9b3890879ad660a62035b7701b88cd3cef53d15eabbb4f53a509a`; 3 settings, 6 jobs, 36 parametric labelled pairs, 4 canonical pairs, 60 protected-Racket evaluations.
- Causal witness SHA-256: `99fbcdd03d0e6a77033a56f31551cbfaba517fef0fc12073df3815518b2ddf15`; protected replay verifies that starting with `got_checkpoint=true` changes the final output.
- Native audit: 10/10 focused tests, 600/600 strict generated examples, 12/12 lessons identifiable, 2/2 causal witnesses firing, zero diagnostic rotation ambiguities.
- Finite probes do not prove universal uniqueness or all-seed sampler completeness. Owner source review, native acceptance, and training admission remain pending and were not claimed.
