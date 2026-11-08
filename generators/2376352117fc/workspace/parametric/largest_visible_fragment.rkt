(rule!
  (let ((dummy 0))
    (define p1 (first (find-color g 1)))
    (define p2 (first (find-color g 2)))
    (define dr (- (first p2) (first p1)))
    (define dc (- (second p2) (second p1)))
    ;; Stage A: exact clipped vector translation.
    (define intermediate
      (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([p (in-list (find-color g 3))])
        (let ((rr (+ (first p) dr)) (cc (+ (second p) dc)))
          (if (in-bounds? rr cc (rows g) (cols g))
              (set-cell out rr cc 8)
              out))))
    (define visible
      (filter (lambda (obj) (= (obj-color obj) 8)) (objects intermediate 0)))
    (define (better? a b)
      (or (> (obj-size a) (obj-size b))
          (and (= (obj-size a) (obj-size b))
               (or (< (obj-r1 a) (obj-r1 b))
                   (and (= (obj-r1 a) (obj-r1 b)) (< (obj-c1 a) (obj-c1 b)))))))
    ;; Stage B: select the unique largest component after clipping.
    (define selected
      (for/fold ([best (first visible)]) ([obj (in-list (rest visible))])
        (if (better? obj best) obj best)))
    (for/fold ([out intermediate]) ([p (in-list (obj-cells selected))])
      (set-cell out (first p) (second p) 4))))
