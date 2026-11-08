(rule!
  (let* ((cmd-cell (last (filter (lambda (cell) (member (third cell) (list 1 2 3 4)))
                                 (grid-cells g))))
         (seed-cell (last (filter (lambda (cell)
                                    (and (not (= (third cell) 0))
                                         (not (member (third cell) (list 1 2 3 4)))))
                                  (grid-cells g))))
         (code (third cmd-cell))
         (color (third seed-cell))
         (delta (cond [(= code 1) (list -1 0)]
                      [(= code 2) (list 1 0)]
                      [(= code 3) (list 0 -1)]
                      [else (list 0 1)])))
    (let walk ([out g]
               [r (+ (first seed-cell) (first delta))]
               [c (+ (second seed-cell) (second delta))])
      (if (in-bounds? r c (rows g) (cols g))
          (walk (if (= (at out r c) 0) (set-cell out r c color) out)
                (+ r (first delta))
                (+ c (second delta)))
          out))))