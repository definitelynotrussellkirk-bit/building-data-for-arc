(rule!
  (let ((starts (filter (lambda (cell) (not (member (third cell) (list 0 1)))) (grid-cells g))))
    (define (draw-dir out start d)
      (let walk ([acc out] [r (+ (first start) (first d))] [c (+ (second start) (second d))])
        (cond [(not (in-bounds? r c (rows g) (cols g))) acc]
              [(= (at g r c) 1) acc]
              [(not (= (at g r c) 0)) (walk acc (+ r (first d)) (+ c (second d)))]
              [else (walk (set-cell acc r c (third start)) (+ r (first d)) (+ c (second d)))])))
    (for*/fold ([out g])
               ([start (in-list starts)]
                [d (in-list cardinal-deltas)])
      (draw-dir out start d))))