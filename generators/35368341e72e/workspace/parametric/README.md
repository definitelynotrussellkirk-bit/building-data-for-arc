# 35368341e72e parametric family

`assembly=query_order` is the exact selected canonical Racket program.
`assembly=fewest_cells_first` keeps the same dictionary/query grammar, decodes
all queried prototypes, measures their nonzero-cell counts, stably sorts the
occurrences by that input-derived count, and galleries them. Repeated keys stay
repeated.

The input stream is setting-independent. It supports 2–6 demonstrations and
exactly four distinct private queries; the last query is a substantive 30×30
case with five spread prototype bands and seven spread query entries. Use
`public_turn(episode, i)` from `prototype.py` to expose one query input at a time.
