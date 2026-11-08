# Odd-class bbox fill → largest orange cluster

The default `bbox_only` setting is the byte-exact canonical rule. The alternate
`largest_orange_cluster` setting is sequential:

1. **A:** group red objects by shape up to rotation and fill the unique
   odd-frequency class's bounding boxes orange.
2. **Intermediate:** the canonical filled grid. Two formerly separate red
   targets now form one 8-cell orange cluster; a third equal-shape target is an
   isolated 4-cell orange cluster.
3. **B:** recompute orange components and recolor only the unique largest one
   blue.

The retained wrong-intermediate program selects one source object before A,
so it cannot see the merged post-fill cluster. The family supports 2–6 demos,
1–4 prefix-stable queries, matched inputs across settings, and a 30×30 query.
