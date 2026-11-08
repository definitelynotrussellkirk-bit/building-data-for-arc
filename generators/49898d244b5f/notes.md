# Current decisions: 49898d244b5f

## Intended transformation and authority

Rebuild a blank output of the same dimensions. A column containing exactly one
nonzero **cell** fills vertically with that cell's color. Columns containing
zero or multiple nonzero cells remain zero, including already-full columns and
multiple cells of one color. The authoritative Racket rule is unchanged and is
pinned by `RULE_HASH = "53c8389bd783"`.

Ordinary positive inputs are rectangular lists of integer colors 0–9, excluding
booleans, with each dimension 3–18 and at least one singleton column. Canonical
inputs pass this domain without metadata exceptions. The three named negative
fixtures have no singleton columns and must fail positive validation; actual
Racket still supplies their blank output labels.

## Reversals in version 2.0.0

The imported 1.1.1 implementation ignored palette controls and enforced narrow
difficulty draw bounds on overrides advertised as 3–18. Its original rationale
is unknown; the imported notes contained no explanation. Exact dimensions,
singleton-column counts, palette counts and aliases are now implemented.
The numeric alias `n_distinct_colors` remains a validated call spelling through
`COMPATIBILITY_ALIASES`, rather than claiming another independent sampled axis.
Unknown controls, invalid integer types, inconsistent aliases and impossible
joint controls fail explicitly. Feasible remaining controls are chosen
constructively. The maximum distinct-color capacity is C + (W−C)H for C
singleton columns in an H×W grid. Values are not silently clamped.

The old validator accepted illegal colors and booleans and did not enforce its
advertised minimum dimensions. The positive-domain validator now checks those
conditions before counting seeds. The old `columns_already_full` comment called
the rule identity; actual Racket returns blank, so that explanation is corrected
and covered by a retained counterexample.

The old optional random distractors rarely distinguished occupied-cell counting
from distinct-color counting. That rival fits every canonical pair. The bounded
baseline Racket probe found 23/24 generated matches; a different 90-draw baseline
population had 83 matches under the independent mirror, with a genuine generated
counterexample separately verified in Racket. Neither population is a production
lesson census.

## Sampling and teaching support

For pure defaults, `(seed + sample_index) % 4` schedules one canonical-profile
example and three adversarial examples. The canonical branch has a 7×7 or 8×8
grid, two distinct colors and two singleton columns. Phase 1 also retains this
size/palette profile while keeping its adversarial distractor; the first repair's
one-profile schedule measured only 13/60 profile hits, below the 25% floor.
Adversarial draws include a
multi-cell monochromatic column reusing an eligible seed color. Occupancy varies
beyond two cells, and eligible columns may share colors. Layouts remain keyed
random draws; full grids are not claimed to repeat with period four.

`EXAMPLES_NEEDED = 3` describes three demonstrations and one query. The four-pair
default window retains distinguishing demonstrations for every query holdout.
The executable lesson guard nevertheless scores the actual labeled pairs. It
reports a rival only when that rival fits every demonstration and changes the
query answer. Six named rivals are checked; four also fit all canonical pairs.
Finite rival evidence does not establish uniqueness against every hypothesis.

Explicit overrides retain priority over teaching preferences. Full capacity,
one-color and all-singleton configurations are lawful where geometrically
feasible, even when they cannot contain every default witness. The fixed
`density="sparse"` token is retained for compatibility and diagnostics, not as a
numeric occupancy ceiling. Helpful texture and palette-kind names are aliases;
negative textures are separate rejection fixtures rather than ordinary modes.

## Reproducers and review evidence

`counterexamples/column_semantics.json` retains five exact actual-Racket-labeled
boundary inputs. `tests/` covers those labels, semantic declarations, controls,
capacity endpoints, malformed inputs, deterministic generation and cyclic query
holdouts. `workspace/probe_column_rules.py` is a portable bounded Racket probe;
`workspace/record_command.py` preserves exact commands, streams and source hashes.

The accompanying review's `REVIEW.md` and `RESULTS.json` state final measured
counts, source hashes, replay commands and any remaining limitations. Historical
failures are retained in that return, including losslessly compressed large
reports. No shared runtime, canonical authority, unrelated generator or approval
record is modified by this repair.

An open shared-heuristic finding remains: the generic minimal-impostor detector
flags lawful singleton and short horizontal-line inputs. The three cases in
`counterexamples/lawful_minimal_inputs.json` and their actual-Racket replay
`workspace/replay_lawful_minimal.py` distinguish horizontal singleton columns
from a vertical multi-cell column. Preserve the valid one-column control. The
warning is reported, not suppressed; the accompanying review states its final
public-gate status and the maintainer decision required.
## Current reviewer considerations

Source SHA-256: `1e258190f411df0ff0f6f487bfa2015564f80747da1fe17991df81bffc8e38a6`.

# Decisions: 49898d244b5f

## Rule and scope

Keep the authoritative Racket program unchanged. It counts occupied cells separately in each column, fills only singleton columns with their seed colors, and constructs the result on a blank grid. Canonical training examples are 7×7 and 8×8 with two distinct singleton seeds; the canonical test is 7×7. No task-specific prior return was used as a repair lead. The selected baseline and the newly collected evidence are the basis for this repair.

The positive generator domain requires rectangular 3–18-row, 3–18-column integer ARC grids, colors 0–9 excluding booleans, and at least one singleton column. These bounds follow the existing advertised domain. Fully empty inputs and inputs containing only multi-cell columns are valid reference-rule boundary cases but remain explicit negative fixtures rather than ordinary positive training inputs. This distinction is tested without special metadata exemptions for canonical examples.

## Controls and constructive feasibility

The old implementation sampled narrow difficulty bands despite advertising larger dimension domains and ignored palette controls. Replace that behavior with exact overrides in every difficulty band. `columns` means the exact count of columns with one nonzero cell. `palette_size` and `n_distinct_colors` mean the same exact number of distinct nonzero colors; inconsistent explicit aliases are errors. After the first after-run identified the duplicate sampled-axis claim, retain `n_distinct_colors` as a validated `COMPATIBILITY_ALIASES` spelling and remove it from independent `AXES`. Both call spellings remain exact and observed. `palette_kind` and the helpful `texture` values are aliases for palette preference, not semantic roles. They must affect real draws. Difficulty biases defaults but cannot narrow the legal override domain.

For height H, width W and singleton count C, at most C + (W−C)H nonzero cells are available while preserving exactly C singleton columns. A request for K distinct colors is feasible only when K is no larger than this capacity. Choose remaining unspecified controls constructively. Do not silently clamp a request or repeatedly sample until a validator accepts it. Reject impossible explicit combinations with the exact conflicting axis names. A single valid advertised override must always have a feasible completion.

Reject unknown controls, invalid fixed enum tokens, booleans/floats/strings supplied as integer overrides, and inconsistent aliases. `None` retains the existing absent-override convention. The fixed position/density axes are explicitly diagnostic. Negative fixture names remain available through `DEGENERATE_TEXTURES` but are excluded from the ordinary helpful-texture domain; their dimensions are honored and their output is blank under Racket.

## Teaching schedule and alternatives

The baseline's optional random distractors usually fail to distinguish a single occupied cell from repeated cells of a single color. All three canonical pairs fit the distinct-color shortcut. The 24-draw actual-Racket baseline probe found only one counterexample. The independent 90-draw baseline probe found seven. This justifies deliberate distinguishing support rather than relying on accidental color collisions.

Use a four-position default schedule, phased by seed plus sample index: one canonical-profile singleton-only example and three adversarial examples. Phase 1 also retains canonical 7×7/8×8 size and two colors, while still including rejected multi-cell columns. The first implementation had only one familiar profile per four positions; the independently pinned profile census measured 13/60 (21.7%), below its 25% envelope floor. A recorded red regression motivated increasing profile support to two of four positions without reducing the three adversarial positions. A repeated-color distractor shares a color with an active singleton, so it distinguishes both local cell counting and the rival requiring globally unique seed colors. Mixed-color distractors and broad geometry provide additional variation where feasible. A three-demonstration/one-query lesson formed from four consecutive draws retains distinguishing demonstrations when any one pair is held out. The category schedule does not imply that full generated grids repeat with period four.

Keep exact override semantics ahead of schedule preferences. A fully occupied set of singleton columns cannot also contain multi-cell distractors; such deliberate overrides are lawful but outside the default teaching guarantee. The lesson guard scores the actual demonstrations and query rather than accepting a lesson solely because its indices belong to a preferred schedule. The portable production census uses the actual shared sampler and saves its materialized pairs. A separate bounded test checks all four cyclic starts and all four query positions for two fixed seeds in all three bands; that mirror-based test complements, rather than replaces, Racket-labeled production evidence.

Reject the alternatives of treating already-full columns as identity, adding another transformation to make the task more complex, or changing the Racket authority to accommodate a generator shortcut. None is supported by the selected task's rule. Preserve the explicit negative cases to prevent those reversals.

## Evidence and stopping criterion

Baseline failures are retained. Semantic tests initially reported 10 failures and 6 passes; control/domain tests reported 45 failures and 8 passes. The command recorder's own regressions include real red and green runs. The before battery is completed evidence, including its failed override gate; its large JSON is losslessly compressed with restoration metadata in `checks/evidence-compression.json`.

Final verification must include the public after battery with required rotations, the explicit portable task-test stage, at least 100 production lessons per band and every query rotation, independent actual-Racket counterexamples, and the exact source patch applied to the preverified fresh extraction. The exposed post-repair solve must bind the same final generator bytes. Two assigned random audits remain read-only observations; they do not imply fixes or approvals of their targets.

The final brief and `RESULTS.json` give measured counts and unresolved limitations. A pass is scoped to the stated domain, sampled populations and named rivals. It is not a proof of general inductive uniqueness, model mastery, or training admission.

## Remaining shared heuristic boundary

The generic minimal-impostor detector warns when this validator accepts a single seed or a short horizontal line. These are lawful inputs, and preserving them is intentional: each occupied column contains exactly one nonzero cell. Three vertical cells in one column instead yield blank output and are rejected from the positive domain. `checks/lawful-minimal-final.json`, the retained three-case JSON and its executable replay establish these distinctions with actual Racket. Do not narrow the generator's legal one-column support to silence that heuristic. The shared detector has not been changed or waived; any remaining public-stage failure is reported explicitly for a maintainer decision. This is the top shared-tool feedback item.
