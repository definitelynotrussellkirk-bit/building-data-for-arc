(rule!
  (let* ((shapes (map (lambda (obj) (subgrid g (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj))) (objects g 0)))
         (h (apply max (map rows shapes)))
         (w (apply max (map cols shapes)))
         (out (grid-from-fn h w
                (lambda (r c)
                  (let ((cnt (count-where (lambda (shape)
                                            (and (< r (rows shape)) (< c (cols shape)) (not (= (at shape r c) 0))))
                                          shapes)))
                    (if (>= cnt 2) 8 0))))))
    (crop-to-content out)))