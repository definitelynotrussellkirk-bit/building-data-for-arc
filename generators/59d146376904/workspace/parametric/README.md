# 59d146376904 parametric family

`summary_order=spatial` is the exact canonical quadrant-majority summary.
`summary_order=majority_count_desc` computes each quadrant's majority color and
count, ranks quadrants by the four input-dependent counts, then emits the colors
in that ranked order. The first two same-size demonstrations use different rank
permutations and crossed nuisance statistics. Four private queries include a
6x8 boundary case and a substantive 30x30 case. See `adversarial_probe.py` for
the bounded named-rival search; finite survival checks are not a universal
uniqueness proof.
