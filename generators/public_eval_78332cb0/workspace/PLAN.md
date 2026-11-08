# Border-contact chain implementation plan
Goal: a general canonical chain-assembly rule and portable two-setting family.
Architecture: split uniform panels using complete color-6 separator bands; ignore foreground colors while matching full contact sets; find the unique head-to-tail horizontal or vertical chain. Alternate prefix_parity recolors foreground in tiles whose cumulative assembled foreground count is odd.
Constraints: all five originals must match; 2..6 demos / 1..4 shuffled-prefix queries; exact integer cells; matched setting inputs; full30x30 scenes and legal output size; native and ordinary extraction closure.
- [x] Tests first: original labels, chain uniqueness, all-border matching, count/type/privacy contracts.
- [x] Python and Racket algorithms, diverse connected panel sampler, native adapter and standalone builder.
- [x] Attack area/color/input ordering, partial-port matching, own/rank/raw-order prefix parity.
- [x] Protected preflight, source-bound audit, causal wrong-intermediate replay, staged tests and package.
Review focus: genuine axis inference rather than input shape; strict whole-set port equality; multiple matching candidates; rectangular panels and thick dividers; cumulative counting depends on reconstructed order.
Ruling: author in this isolated packet only, preserve gold and immutable parent, no owner registration or acceptance claims.

Final review: author self-review (no independent subagent review). Tests and protected checks are retained in checks/public_eval_78332cb0/. Owner acceptance is pending.
