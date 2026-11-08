;; LEGACY — Python-evaluator-only predicates.
;; Don't add to this file; new primitives go in arc-prelude.rkt.

(define (obj-is-dot?* obj) (= (obj-size obj) 1))
(define (obj-is-rectangular?* obj)
  (let ((bbox (obj-bbox obj)))
    (= (obj-size obj)
       (* (+ 1 (- (nth bbox 2) (nth bbox 0)))
          (+ 1 (- (nth bbox 3) (nth bbox 1)))))))
(define (obj-is-line?* obj)
  (let ((bbox (obj-bbox obj)))
    (or (= (nth bbox 0) (nth bbox 2))
        (= (nth bbox 1) (nth bbox 3)))))
