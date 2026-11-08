(rule!
  (let* ((origin (first (find-color g 5)))
         (xmark (first (find-color g 6)))
         (vx (list (- (first xmark) (first origin))
                   (- (second xmark) (second origin))))
         (tip (list (+ (first origin) (* 2 (first vx)))
                    (+ (second origin) (* 2 (second vx))))))
    (paint-cells g (list origin xmark tip) 8)))