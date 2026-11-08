# public_eval_36a08778 — current authoring design

Parent rule: magenta top-edge rays fall through orange cells. On first contact
with a contiguous horizontal red segment, a ray paints the row above from one
cell beyond each end and continues down from the in-bounds endpoint columns.
All six train labels and both private-gold test labels are explained by this rule.

Native parameter `routing_mode=split|closest_exit`; split is canonical. The
input-dependent intermediate is each hit segment plus its impact column(s), and
the next cap/branch operation consumes those values. Fresh scenes vary source
counts, obstacle lengths, boundary clipping, distractors, recursion depth and
include a substantive 30x30 query. Owner registration and acceptance are pending.
