# Direct public parent edb79dae

The reference finds the unique modal background and hollow rectangular frame, reads exterior arrow tiles as a directed color map, groups all remaining exterior cells by original color into templates (including disconnected pieces), replaces each solid square in the frame with its matching template, applies one simultaneous color-map step, and crops the frame inclusively.

The supplied originals comprise two labelled training pairs and one public test solution in `shared/data/raw/arc-agi_evaluation_solutions.json`. Both once and terminal mapping fit the training pairs, but the public test gold resolves the ambiguity: once matches exactly, while terminal differs in88cells. The default is therefore the once rule, validated against all three supplied labelled originals. Solution data is used only for private authoring validation and is never read by generator.py, family.py or the Racket reference. The color8 template in the public test has15cells in components13 and2; both are preserved.

The episode-fixed family teaches once versus terminal mapping on matched fresh inputs. A four-edge chain distinguishes terminal from two/three hops; a second, branching legend with two sinks refutes painting every template one global terminal color. Input palettes, masks, source counts, source placement, occupied frame slots, tile sizes and query order vary. Queries are kept in a separate deterministic stream, with one substantive30×30 scene. Supported counts are2–6 demos and1–4 queries; default4 queries. Generated square template sizes are3–5. Cyclic maps, overlapping arrows, multiple frames and mixed-size blocks are outside the authored grammar.

This candidate is unapproved. Original-pair execution, generated-label checks, authoring preflight, owner registration/native qualification and training admission are distinct claims.

Owner runtime decision: canonical authority is `ee_edb79dae`; the descriptive home stays `public_eval_edb79dae`. The explicit `RULE_TASK_ID` satisfies the existing reference identifier contract without changing the Racket program or sampler.

## Current refinement: 2026-10-25
Preserved the exact reference and production generator. Native template masks now receive independent seed-derived D4 orientations; this removes the fixed disconnected-root orientation while keeping template identity and the arrow grammar unchanged. Added a full-bank presentation module with a separate presentation seed, single-query content-hashed public views, strict payload validation and duplicate rejection before directory creation. Legacy public_turn now strips demonstration metadata too. Native and production samples need not be byte-identical; both remain checked against the preserved reference.

Verification: 32 task tests plus nine handoff-tool tests; bounded 32-seed audit across all demo counts 2..6 (320 lessons, 2,560 pairs), 20 rivals, no harmful survivors. Authoring preflight passed all three supplied original labels and both settings at seeds 17/43; protected wrong-order replay changed 12 cells; 16 public views and six generator-only relocation labels passed. No owner qualification, acceptance or training admission is claimed.

The inherited original-label test now reads a task-owned private fixture rather than searching its ancestors for shared raw data. Both complete task suites pass when copied without shared original-data directories. The fixture is not read during generation; official labels are independently checked from immutable shared data by preflight.
