(rule!
  (let ((out (empty-grid (rows g) (cols g) 0)))
    (for/fold ([cur out]) ([obj (in-list (objects g 0))])
      (for*/fold ([acc cur]) ([r (in-range (obj-r1 obj) (+ (obj-r2 obj) 1))]
                              [c (in-range (obj-c1 obj) (+ (obj-c2 obj) 1))])
        (cond [(or (= r (obj-r1 obj)) (= r (obj-r2 obj)) (= c (obj-c1 obj)) (= c (obj-c2 obj)))
               (set-cell acc r c (obj-color obj))]
              [else
               (set-cell acc r c (if (= (modulo (+ (- r (+ (obj-r1 obj) 1)) (- c (+ (obj-c1 obj) 1))) 2) 0)
                                     (obj-color obj)
                                     0))])))))