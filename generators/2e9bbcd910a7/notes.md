# Working notes: 2e9bbcd910a7

## Current decision — 2026-10-24

- Keep `paint_target=winner` as the byte-exact canonical default (program SHA-256 `36b1943f55f3b91988fa7f9281423f9d5c9e770f11009d2197912c2b04ae11fc`).
- Add one nearby non-collapsing setting, `paint_target=crossing_follower`: A canonically ranks/selects the longest diagonal; its exact cells, direction and length are the intermediate; B paints the highest-ranked strictly shorter opposite-direction run that crosses those cells.
- Generate matched 10×10 inputs across settings with 2–6 demonstrations and 1–4 independent queries. The six constructive templates cover both diagonal directions and winner lengths 6, 7 and 8. A 30×30 extension was rejected because every canonical pair and the approved generator grammar are fixed 10×10; enlarging would broaden rather than stress the admitted domain.
- A bounded sampler stress over seeds 0–49 at the minimum and maximum demo profiles completed 200/200 episodes (1,600 pairs) with no construction failures, duplicate episode inputs, grammar violations or setting-input mismatches.
- Plant a stronger global runner-up and a stronger non-crossing opposite-direction run in every scene. The bounded audit over seeds 0 and 17 reports 28 pairs and rejects the canonical winner, global runner-up and opposite-direction champion shortcuts wherever relevant; this is finite-rival evidence, not universal uniqueness.
- Use `public_challenge`, `public_turn` and `controller_turns` for the model-visible projection. Each turn exposes all demonstrations and exactly one query input; settings, seeds, Racket source and query answers remain private. The first turn is byte-identical to a one-query episode from the same seed.
- Native qualification is current at `checks/2e9bbcd910a7/qualification/qualification.json`; the four-case protected-Racket wrong-intermediate replay is `checks/2e9bbcd910a7/causal/witness.json`.
- Reviewer status is **ready**, not accepted. Next useful action: integrate these exact bytes, rerun native qualification/witness replay, and perform owner acceptance. Training admission remains a separate downstream decision.
