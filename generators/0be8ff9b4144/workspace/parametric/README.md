# 0be8ff9b4144 intersection-policy family

This proposed native family keeps the source task's header decoding and
intersection construction. `intersection_policy` is fixed for an episode:

- `all`: exact canonical Racket bytes; paint the complete Cartesian product.
- `same_parity`: order the active rows and columns, then paint pairs whose ranks
  have equal parity.
- `opposite_parity`: paint pairs whose ranks have different parity.

The sampler is independent of the setting. It supports 2–6 demonstrations and
1–4 queries; a one-query request is the exact prefix of the four-query episode.
The four-query curriculum contains 12×14, 18×25, 25×18, and substantive 30×30
inputs. Wrong-color header decoys, occupied intersections, off-intersection
content, irregular rank/coordinate parity, and boundary markers attack common
shortcuts. Labels are independently replayed by the native protected-Racket
qualification worker.
