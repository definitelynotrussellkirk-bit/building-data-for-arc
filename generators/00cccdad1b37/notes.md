# Working notes: 00cccdad1b37

## Current decision

The canonical `route_segment=whole` setting remains byte-for-byte identical to the catalog rule. The native nearby variant is `route_segment=after_gate`: step A derives the mandatory whole-route cells and selects an input-dependent midpoint gate; step B recomputes and paints the mandatory gate-to-goal suffix. Sampling is independent of the setting, supports 2–6 demonstrations and four distinct queries, and includes a substantive 30×30 query.

## Self-review result

The focused finite rival audit rejects whole-route/suffix confusion, a fixed midpoint, a single chosen shortest path, and painting all shortest-path cells on the retained demonstrations and queries. Protected Racket agrees with generated labels for both settings. The public projection exposes one query at a time, has private-field invariance and positive-control coverage, and retains no hidden setting/program/answer fields.

## Limits and next action

These are bounded authoring checks, not a universal uniqueness proof. The source-bound authoring preflight and causal replay grant neither owner acceptance nor training admission. One earlier packet-controlled test attempt stalled transiently during protected-Racket startup; the retained exact-source rerun completed 23/23. Next: integrate the exact patch, verify the manifest/source binding, rerun native owner qualification and protected causal replay, then perform fresh owner acceptance.
