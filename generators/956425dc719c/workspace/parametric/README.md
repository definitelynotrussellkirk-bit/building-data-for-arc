# `956425dc719c` parametric post-filter family

`post_select` is fixed once per episode.

- `none` — exact canonical default: recolor orange components touching exactly one border gray.
- `largest` — run canonical stage A, then paint the unique largest remaining orange component blue.
- `smallest` — run canonical stage A, then paint the unique smallest remaining orange component blue.

Generated scenes vary the survivor-rank profiles across `(2,4,7)`, `(3,6,9)`, `(1,5,8)`, and `(4,7,10)`. In every profile, a larger one-border component is removed by stage A, so ranking before filtering is an observable wrong-order rival and no fixed component size solves the minimum lesson. The sampler gives the six training and four query slots disjoint visible indices, uses identical inputs across settings, keeps the four-query bank stable as demo count changes, and includes a substantive 30×30 final query.
