"""Named private alternatives; every demo and query is executed by the auditor."""

KEEP = """(define (keep-hole? record)
      (or (equal? fill-scope 'all)
          (= (third record) (hash-ref maxima (second record)))))"""


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise ValueError("rival transformation no longer matches exactly one source site")
    return source.replace(before, after)


def selection(source, predicate):
    return replace_once(source, KEEP, "(define (keep-hole? record) " + predicate + ")")


def programs(adapter, settings):
    source = adapter.program(settings)
    other = "largest_per_owner" if settings["fill_scope"] == "all" else "all"
    smallest = replace_once(source, "(max old area)", "(min old area)")
    return {
        "other_scope": adapter.program({"fill_scope":other}),
        "reverse_lookup": replace_once(source, "(define legend-reading 'edge)", "(define legend-reading 'reverse)"),
        "fixed_top_left_lookup": replace_once(source, "(define legend-reading 'edge)", "(define legend-reading 'fixed_top_left)"),
        "eight_neighbor_closure": replace_once(source, "(objects g -1)", "(objects-8 g -1)"),
        "largest_globally": selection(source, "(= (third record) (apply max (map third (filter (lambda (r) (hash-has-key? mapping (second r))) holes))))"),
        "smallest_per_owner": selection(smallest, "(= (third record) (hash-ref maxima (second record)))"),
        "first_per_owner": selection(source, "(equal? record (find-first (lambda (r) (= (second r) (second record))) holes))"),
        "last_per_owner": selection(source, "(equal? record (find-first (lambda (r) (= (second r) (second record))) (reverse holes)))"),
    }
