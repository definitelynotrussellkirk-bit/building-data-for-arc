(rule!
  (let ((starts (filter (lambda (cell) (not (member (third cell) (list 0 1)))) (grid-cells g))))
    (define (draw-dir out start d)
      (let walk ([acc out] [r (+ (first start) (first d))] [c (+ (second start) (second d))])
        (cond [(not (in-bounds? r c (rows g) (cols g))) acc]
              [(= (at g r c) 1) acc]
              [(not (= (at g r c) 0)) (walk acc (+ r (first d)) (+ c (second d)))]
              [else (walk (set-cell acc r c (third start)) (+ r (first d)) (+ c (second d)))])))
    (define stage
      (for*/fold ([out g])
                 ([start (in-list starts)]
                  [d (in-list cardinal-deltas)])
        (draw-dir out start d)))
    (define walls (find-color g 1))
    (define top (apply min (map first walls)))
    (define bottom (apply max (map first walls)))
    (define left (apply min (map second walls)))
    (define right (apply max (map second walls)))
    (define guessed (third (first starts)))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (let ((v (at stage r c)))
          (if (and (= v 0) (< top r) (< r bottom) (< left c) (< c right))
              guessed
              v))))))
