# Working notes: 86e4139d27c1

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/86e4139d27c1/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Reviewer decision — native survivor-route family (2026-10-24)

The canonical `plus_only` setting returns the selected canonical program byte-for-byte. The alternative `survivor_route` setting first paints the canonical clipped green plus from the first two row-major blue markers, then recomputes blue markers on that intermediate grid and routes vertically first toward the first surviving marker. The route preserves the first plus arm and the target marker, so Stage B depends on a post-Stage-A coordinate rather than a preselected decoration.

The admitted grammar uses exactly three blue markers, reserves colors 3 and 8 for outputs, accepts 3×3 through 30×30 exact-integer grids, supports 2–6 demonstrations, and always emits four distinct setting-neutral query inputs. The last query is a substantive 30×30 scene with distractors. Input generation is deterministic by seed and isolated from global RNG state.

Teaching checks use demonstrations only against the finite declared set: `plus_only`, `survivor_route`, original-first/second/third targets, last-survivor, horizontal-first, paint-first-step, and paint-target. Across seeds 0 and 17 with 2, 3, and 6 demonstrations, only the selected setting survived. This is a bounded rival audit, not a universal uniqueness claim.

A strict parser check found and removed one trailing delimiter from the initial alternative Racket source; the ordinary wrapper had ignored that suffix, while admission correctly rejected it. Final hashes are adapter `484f72e3282233298a014890d204422683eda5b6e19c9e5c665822b2bdfdb546`, alternative Racket `26981488834482dc123d8a375f523757a0a8f6e83fd7c4cf730057c4da38e4fc`, inventory `284fef0c4f7c7789b0da6664bf570c0bdc73cabd7e01957ba1cd16e4e9fca66a`, qualification `ad3c8d9d5b3e22524d2ec1d0d425eb8ce88ed666775e5c0465dee351f2b050a5`, and witness `ecb2bcd444ff6eff6d65343b5ee0336317b180139e88d6fa36ed8896eb0e9b75`.

Final evidence: `checks/86e4139d27c1/qualification/`, `checks/86e4139d27c1/sequential-witness/`, and `checks/86e4139d27c1-tests/result.json`. The next action is owner integration followed by fresh native qualification, causal replay, and acceptance on exact live bytes. No training admission is claimed. Optional peers were not reviewed in this return.
