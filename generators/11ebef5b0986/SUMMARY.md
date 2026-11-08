# 11ebef5b0986 — Eight-Way Room Weave

Version: `3.0.0`. Canonical rule pin: `37be31441b18`.

A black canvas contains three distinct palette colors from **2..8**, in order at row 0, columns 1..3; one closed blue (1) rectangular frame; and exactly one maroon (9) seed strictly inside it. From the seed, paint all eight cardinal/diagonal rays, cycling the three legend colors by distance and stopping at the actual blue frame. Preserve the legend, seed and frame. Training labels continue to come from the canonical Racket rule, not the diagnostic Python mirror.

## Input distribution

Ordinary consecutive samples use a three-slot teaching schedule. Slot 0 has canonical-scale geometry and a palette containing gray 5. Slot 1 has a frame inset far enough to leave a blank stripe beyond its wall. Slot 2 has a corner seed in a larger room, exposing a ray beyond distance seven. Each ordinary three-demo window therefore provides evidence against the two explicitly implemented rivals: fixed canvas clipping and a seven-step ray cap. This is a finite-rival statement, not proof of unique induction.

The declared override domain is height 7..16, width 8..16, frame mode `fit|inset`, seed placement `random_interior|corner`, and palette kind `default|warm_palette|cool_palette|varied_palette`. All declared combinations are supported across difficulty bands. Overrides may intentionally remove teaching witnesses; the ordinary-window guarantee does not apply to arbitrary overridden scenes. Unknown axes are rejected. Former constant/inert axes and invalid-input textures are no longer advertised.

Palette pools: default samples 3 distinct colors from 2..8; warm uses {2,4,6,7}; cool uses {3,5,6,8}; varied includes 5 and two other legal colors. Difficulty affects ordinary long-ray dimensions, not the legal override range. Palette RNG is keyed by difficulty to reduce duplicate scenes across bands.

## Verification and boundaries

The review return for `review-5fa7fbe55f2eb5ca` retains a 12-stage green battery, 57 explicit task-local tests, and a final-source Racket census: 900/900 valid nonidentity draws, 886 unique inputs, zero parity failures, and both named rivals refuted in all 780 overlapping three-demo windows (easy/medium/hard, seeds 0..19, sample indices 0..14, no overrides). These counts are finite observations, not approval of the library or a claim of exhaustive correctness.

The canonical ledger and Racket semantics were unchanged. One redundant comment was removed from the bound base-authority `racket_target.target_code` to restore exact authority synchronization. Catalog approval remains independently derived; no approval flag was edited.

Run task-local tests explicitly; the root repository suite does not discover them. See `workspace/README.md` for the reusable Racket-backed census and audit probes.
