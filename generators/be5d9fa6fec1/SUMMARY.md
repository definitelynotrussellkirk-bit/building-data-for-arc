# be5d9fa6fec1

Version `3.0.0` is a constructive curriculum for the canonical row-transition-group rule.

Inputs use one of the five canonical `(height, width, maximal-group-count)` profiles. Each maximal group contains `1..3` identical rows; adjacent groups alternate between a nonempty `0/1` row and a nonempty `0/8` row. Group zero has at least two rows. Number maximal groups from zero and, in groups `0, 3, 6, ...`, recolor every nonzero cell to `2`; preserve all other cells.

Public exact controls are `profile_id` (`0..4`) and `start_kind` (`mix|eight`). Both are recoverable from the final pixels; unknown and invalid overrides are rejected, and unknown difficulty values fail explicitly at the public boundary. The generator pins canonical `RULE_HASH = "0ff6975f3e81"`, declares a strict grammar and six executable semantic rivals, and uses three demonstrations per lesson.

The independent analyzer/oracle is `workspace/reference_probe.py`; task-local regressions are in `tests/test_generator.py`.

Kind: `per_puzzle`. Selected version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
