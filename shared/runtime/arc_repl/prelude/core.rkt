;; LEGACY — Python-evaluator-only helpers.
;; The canonical Racket bridge loads `racket_prelude/arc-prelude.rkt`,
;; not this file. Nothing here is callable from a grounded rule run in
;; Racket mode. Kept so the Python evaluator fallback still resolves
;; these names. Don't add to this file; new primitives go in
;; arc-prelude.rkt.

(define (second lst) (nth lst 1))
(define (min-of-list lst) (reduce min (first lst) (cdr lst)))
(define (max-of-list lst) (reduce max (first lst) (cdr lst)))
(define (sum lst) (reduce + 0 lst))
(define (average lst) (/ (sum lst) (length lst)))
(define (repeat val n) (for/list (i (range 0 n)) val))
(define (pairs lst) (zip-lists (cdr lst) lst))
