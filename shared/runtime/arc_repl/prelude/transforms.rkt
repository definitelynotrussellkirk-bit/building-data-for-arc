;; LEGACY — Python-evaluator-only transforms.
;; Don't add to this file; new primitives go in arc-prelude.rkt.

;; Gravity: drop non-zero cells downward in each column
(define (gravity-down grid)
  (map-cols grid (lambda (col)
    (let* ((vals (filter (lambda (v) (!= v 0)) col))
           (pad (- (length col) (length vals))))
      (append (repeat 0 pad) vals)))))

;; Gravity up
(define (gravity-up grid)
  (map-cols grid (lambda (col)
    (let* ((vals (filter (lambda (v) (!= v 0)) col))
           (pad (- (length col) (length vals))))
      (append vals (repeat 0 pad))))))

;; Count unique non-zero colors
(define (num-colors grid)
  (length (grid-colors grid)))

;; Check if grid is all one color
(define (uniform? grid)
  (<= (num-colors grid) 1))

;; Extract the bounding box of non-zero content
(define (content-bbox grid)
  (let ((cells (filter-cells grid (lambda (r c v) (!= v 0)))))
    (if (null? cells)
      (list 0 0 0 0)
      (list (min-list (map fst cells))
            (min-list (map snd cells))
            (max-list (map fst cells))
            (max-list (map snd cells))))))
