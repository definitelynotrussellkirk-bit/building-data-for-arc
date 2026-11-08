# Working notes: b7564fb4b95d

## Review 2026-10-25 — assignment `review-9432a0bfd332a6c9`

### Base repair

The imported generator did not provide a trustworthy control or validation
contract. It omitted `RULE_HASH`, ignored every advertised override, accepted
invalid scalar types and unsupported difficulties, and its `self_check` accepted
minimal one-color impostors. The review replaced it with version 2.0.0, pinned to
canonical rule hash `dfa4e91b5010`, while preserving all five original labels.

The repaired exact axes are `grid_h` (11–30), `grid_w` (14–30), `n_frames`
(1–3), and `command_code` (1–4). Unknown axes, non-exact scalar types and invalid
difficulties fail loudly. The generator now parses selector, command marker and
hollow frames structurally, mirrors the canonical transformation, validates the
actual demonstrated grammar, and is deterministic under its keyed RNG. Ordinary
default draws retain canonical-scale 5x5/6x5 frames; an explicitly requested
30x30 three-frame case uses distributed large frames for meaningful stress.

A test-first repair locked each defect, all original pairs, override boundaries,
strict typing, malformed/impostor rejection, canonical-scale defaults and 30x30
stress. Final lint, self-check, defect lint and the exact override matrix passed;
the override matrix accepted 5,220/5,220 draws over 58 cases and all three bands
with zero findings or warnings.

### Native parametric family

The canonical setting `transform_order=command_only` selects and normalizes the
source shape, applies command code 1/2/3/4, then stamps that orientation into each
frame. The added setting `transform_order=command_then_reflect` consumes the
command-oriented shape and horizontally reflects that intermediate before
stamping. Commands 2 and 4 plus asymmetric source shapes make this order
observable. The protected counterfactual reflects first and then applies the
command; its different Racket output is the causal witness.

`workspace/parametric/prototype.py` supports independently requested 2–6
demonstrations and 1–4 queries, deterministic matched inputs, stable prefixes and
four distinct queries. The fourth query is exactly 30x30 with three substantive
frames. Constructive candidate filtering uses input geometry only and ensures each
visible lesson separates both settings and declared wrong-order/identity
shortcuts.

The reusable protected-Racket audit checked seeds 0, 17 and 97 at 2, 3 and 6
demonstrations: 18 reports, 61 Racket labels and zero surviving declared
shortcuts. Current-source authoring preflight, causal replay, sequential public
projection, first-turn privacy checks and 39 focused tests passed. This is a
reviewer-reported ready family; owner native qualification, acceptance and any
training admission remain separate.
