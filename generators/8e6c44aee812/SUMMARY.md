# 8e6c44aee812

Read the main diagonal of the square nested-L staircase. Strip an optional trailing zero padding band, then double the input height and width. Output cell (r,c) is active_diagonal[max(r,c) modulo period]. Repeated active colors are lawful and the final zero is optional.

Kind: `per_puzzle`. Reviewed version: `3.1.0`.

Five demonstrations and one query use a declared 12-slot curriculum. Repeated
first and later colors provide redundant evidence under each query holdout.
All three exact pattern classes, periods 4..9, and both padding choices remain
available. Literal integer controls reject silent coercion. Racket authority
`2f49d92711a1` is unchanged; see `notes.md` and `workspace/README.md` for decisions
and reproducible checks.
Approval is derived by the catalog from current code and retained evidence.
