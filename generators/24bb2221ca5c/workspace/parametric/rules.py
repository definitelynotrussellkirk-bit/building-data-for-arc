"""Exact canonical and topology-dependent hole-selection Racket programs."""
from __future__ import annotations

from pathlib import Path


POLICIES = ("all", "largest_hole_area", "most_holes")

_CANONICAL_TAIL = '(for/fold ((out g)) ((obj (in-list (objects g 0)))) (let* ((cg (component-grid obj)) (holes (holes-in-binary (binary-grid cg))) (bb (obj-bbox obj))) (for/fold ((acc out)) ((p (in-list holes))) (set-cell acc (+ (first bb) (first p)) (+ (second bb) (second p)) (obj-color obj)))))))'


def _policy(settings: dict) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"fill_policy"}
        or type(settings["fill_policy"]) is not str
        or settings["fill_policy"] not in POLICIES
    ):
        raise ValueError(
            "settings must contain exactly one declared fill_policy: "
            "all, largest_hole_area, or most_holes"
        )
    return settings["fill_policy"]


def canonical_program() -> str:
    """Return the exact registered program, preserving every source byte."""
    return Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")


def _selector_tail(policy: str) -> str:
    score = (
        "(length (second record))"
        if policy == "largest_hole_area"
        else "(length (third record))"
    )
    return f"""    (define (hole-regions-in-binary grid)
      (let loop-pos ([positions (grid-positions grid)] [seen (list)] [acc (list)])
        (cond [(empty? positions) (reverse acc)]
              [(or (member? (first positions) seen)
                   (not (= (at grid (first (first positions)) (second (first positions))) 0)))
               (loop-pos (rest positions) seen acc)]
              [else
               (let bfs ([queue (list (first positions))]
                         [seen2 (cons (first positions) seen)]
                         [cells (list)]
                         [touches #f])
                 (if (empty? queue)
                     (loop-pos (rest positions) seen2
                               (if touches acc (cons (reverse cells) acc)))
                     (let* ((cur (first queue))
                            (r (first cur))
                            (c (second cur))
                            (border (or (= r 0) (= c 0)
                                        (= r (- (rows grid) 1))
                                        (= c (- (cols grid) 1))))
                            (nbrs
                             (filter
                              (lambda (p)
                                (and (in-bounds? (first p) (second p) (rows grid) (cols grid))
                                     (not (member? p seen2))
                                     (= (at grid (first p) (second p)) 0)))
                              (map (lambda (d) (list (+ r (first d)) (+ c (second d)))) dirs4))))
                       (bfs (append (rest queue) nbrs)
                            (append seen2 nbrs)
                            (cons cur cells)
                            (or touches border)))))])))
    (define candidates
      (filter
       (lambda (record) (not (empty? (second record))))
       (map
        (lambda (obj)
          (let* ((cg (component-grid obj))
                 (regions (hole-regions-in-binary (binary-grid cg)))
                 (holes (if (empty? regions) (list) (apply append regions))))
            (list obj holes regions)))
        (objects g 0))))
    (define (score record) {score})
    (define chosen
      (if (empty? candidates)
          #f
          (for/fold ([best (first candidates)]) ([record (in-list (rest candidates))])
            (if (> (score record) (score best)) record best))))
    (if (equal? chosen #f)
        g
        (let* ((obj (first chosen))
               (holes (second chosen))
               (bb (obj-bbox obj)))
          (for/fold ([out g]) ([p (in-list holes)])
            (set-cell out (+ (first bb) (first p)) (+ (second bb) (second p)) (obj-color obj)))))
  ))"""


def program(settings: dict) -> str:
    """Materialize one fixed rule; the default is byte-identical to canonical."""
    policy = _policy(settings)
    source = canonical_program()
    if policy == "all":
        return source
    if source.count(_CANONICAL_TAIL) != 1 or not source.endswith(_CANONICAL_TAIL):
        raise ValueError("canonical final hole-fill block changed or is ambiguous")
    return source[: -len(_CANONICAL_TAIL)] + _selector_tail(policy)
