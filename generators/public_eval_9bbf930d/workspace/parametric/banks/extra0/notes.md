# 9bbf930d — stateful rail guidance, authoring v1.0.0

## Current rule
An initial magenta (6) marker in the left column moves right only when the first
non-orange evidence in its three-row strip is an equal-color rail pair flanking
an orange (7) center. It moves straight through orange. Equal-color perpendicular
flanks update its guidance color. A blocking wall of the current guidance color
permits a turn only when exactly one perpendicular neighbor is open orange.
A different wall, ambiguous/blocked turn, or boundary stops the marker. Repeated
(position, heading, guidance) states terminate. All markers trace the immutable
input independently; moving sources are cleared and endpoints painted together.

The third original training pair transfers a gray-guided marker to yellow rails
before its next turn: freezing the initial color fails that original label.
`guidance=adaptive` is the canonical reference and `guidance=initial` freezes the
initial rail color. All three training labels and the supplied test gold match
the canonical general Python and protected-Racket implementations.

## Sampler and substantive dependency
Settings share inputs, with 2–6 independently prefix-stable demonstrations and
1–4 prefix-stable queries from a privately shuffled four-query bank. Scenes
contain two color-handoff corridors, inactive unequal-color entrance rails, and
an optional third straight route. Colors and vertical reflection vary. Black
walls are legal. The first demonstration and every even demonstration contain
a four-turn route, as does the 30×30 stress query. In the 32-seed audit the stress
inputs have at least 259 non-orange cells and boundary contact.
A reads the input-derived sequence of rail-color handoffs. B uses the current
guidance at each collision to decide whether to turn. A protected counterfactual
freezes initial guidance on an actual preflight pair, changing the endpoint grid;
a second protected execution replays the result.

## Adversarial repairs and retained counterexample
An early sampler taught only paths with at most two turns. A failing 32-seed
regression exposed this curriculum limit. The repaired first demonstration and
stress query explicitly exercise four turns. The added `two_turn_budget` rival
matches both retained old demonstrations, fails the legal expanded four-turn
query, and fails the first repaired demonstration. Ten protected-Racket
executions, exact inputs/outputs and source bindings are retained in
`checks/public_eval_9bbf930d/turn-budget-regression.json`. The old sampler did not
itself emit the four-turn query: this is a documented curriculum extension,
not a falsely claimed old in-distribution mismatch.

The rival is observationally equivalent to `initial` on this admitted generated
domain; it is not falsely reported refuted there. Teaching certificates instead
reject it for `adaptive` and check that any surviving hypothesis agrees on all
queries. The finite set cannot prove universal identification.

The ordinary generator's episode-shaped return was also repaired to the native
input-only `(seed, sample_index, difficulty=...)` protocol after failing tests.
Both wrappers have relocation, parameter validation and size-band regressions.

## Verified scope and bounds
49 task tests pass; the combined suite passes 96 tests. The 32-seed two-setting
audit covers 64 episodes, 1,280 supported prefixes, 256 public views, 640 finite
rival comparisons and 280 protected-Racket evaluations. Ten named rivals leave
no dangerous survivor. Original examples exercise interactions beyond the
constructed independent-corridor sampler; the latter is not claimed to cover
all legal crossing, cyclic, or arbitrary branching layouts.

Authoring preflight passes both settings, seeds 17 and 43, two demonstrations
and four queries, plus all four original labels. The current 155-file preflight
binding matches the causal witness and replay; the audit independently binds
13 task files. Sixteen retained one-query exports pass the saved-byte checker.

## Reproduction and next owner action
Run `python3 -m pytest --import-mode=importlib -q generators/public_eval_9bbf930d/tests`
in the packet's protected environment. `workspace/parametric/audit_native.py`
accepts `--seeds`, `--racket-seeds`, and a fresh `--out`; the companion
`authoring_witness.py` rejects stale/unsafe source or preflight evidence before
constructing and replaying the causal test. Exact commands are in RESULTS.json.

Reviewer-ready, owner-pending. Catalog-backed staged tests stop at “Unknown
puzzle” because this is an unregistered home; the complete direct tests pass.
Owner registration/source review, native qualification and fresh acceptance
remain separate. No shared authority was altered, no training admission or
benefit is claimed, and final review was author self-review.
