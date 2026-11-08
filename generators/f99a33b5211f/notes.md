# Working notes: f99a33b5211f

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 parametric family

- Preserved the exact canonical default as `axis=x`; its program SHA-256 is `871e78062f00b05135db3f0b5e56209eca48b34f30ebed1e78aade8546fc7d38`.
- Added the nearby `axis=y` rule on matched inputs. A color-5 origin with color-6 and color-7 unit markers defines an arbitrary local frame; the setting selects which input-derived axis is extended to a three-cell color-8 bar.
- The minimum two demonstrations change both local vectors and reject paint-both-axes, origin-only, marker-only, and every fixed global direction. Four-query banks include a 30×30 scene with 22 separated distractor components, all five distractor colors, and at least 100 distractor cells.
- The required A→intermediate→B dependency is: recover `{origin, selected_marker, vector, tip}` from the frame, then paint exactly the derived origin, marker, and tip. A protected wrong-intermediate witness substitutes the x-axis record into a y-axis episode and changes the final output.
- A 32-seed audit checked 320 generated pairs, all 2–6 demo and 1–4 query prefixes, four directions for each local axis, declared rivals, and 32 substantive 30×30 banks. Target tests pass 20/20, including ordinary generator preservation and protected-Racket parity.
- `workspace/parametric/preflight_compat.py` contains the same bounded legacy single-test normalization needed by the shared preflight; no shared source or canonical authority was changed.
- Reviewer work is ready; exact-source owner integration, fresh native qualification, acceptance, and any training admission remain separate and pending.
