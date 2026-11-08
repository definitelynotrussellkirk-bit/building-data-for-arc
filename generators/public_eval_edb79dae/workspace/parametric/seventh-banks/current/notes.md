# Direct public parent edb79dae

The reference finds the unique modal background and hollow rectangular frame, reads exterior arrow tiles as a directed color map, groups all remaining exterior cells by original color into templates (including disconnected pieces), replaces each solid square in the frame with its matching template, applies one simultaneous color-map step, and crops the frame inclusively.

The supplied originals comprise two labelled training pairs and one public test solution in `shared/data/raw/arc-agi_evaluation_solutions.json`. Both once and terminal mapping fit the training pairs, but the public test gold resolves the ambiguity: once matches exactly, while terminal differs in88cells. The default is therefore the once rule, validated against all three supplied labelled originals. Solution data is used only for private authoring validation and is never read by generator.py, family.py or the Racket reference. The color8 template in the public test has15cells in components13 and2; both are preserved.

The episode-fixed family teaches once versus terminal mapping on matched fresh inputs. A four-edge chain distinguishes terminal from two/three hops; a second, branching legend with two sinks refutes painting every template one global terminal color. Input palettes, masks, source counts, source placement, occupied frame slots, tile sizes and query order vary. Queries are kept in a separate deterministic stream, with one substantive30×30 scene. Supported counts are2–6 demos and1–4 queries; default4 queries. Generated square template sizes are3–5. Cyclic maps, overlapping arrows, multiple frames and mixed-size blocks are outside the authored grammar.

This candidate is unapproved. Original-pair execution, generated-label checks, authoring preflight, owner registration/native qualification and training admission are distinct claims.

Owner runtime decision: canonical authority is `ee_edb79dae`; the descriptive home stays `public_eval_edb79dae`. The explicit `RULE_TASK_ID` satisfies the existing reference identifier contract without changing the Racket program or sampler.
