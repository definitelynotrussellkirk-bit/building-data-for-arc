(rule!
  (let* ((origin (first (find-color g 5)))
         (ymark (first (find-color g 7)))
         (vy (list (- (first ymark) (first origin))
                   (- (second ymark) (second origin))))
         (tip (list (+ (first origin) (* 2 (first vy)))
                    (+ (second origin) (* 2 (second vy))))))
    (paint-cells g (list origin ymark tip) 8)))
