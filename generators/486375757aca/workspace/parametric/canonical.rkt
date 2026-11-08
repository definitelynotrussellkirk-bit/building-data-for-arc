(rule!
  (for/fold ([out g]) ([obj (in-list (filter (lambda (o) (= (obj-color o) 1)) (objects g 0)))])
    (let ((seed
           (first (reverse (filter (lambda (v) (not (member v (list 0 1))))
                             (for*/list ([r (in-range (+ (obj-r1 obj) 1) (obj-r2 obj))]
                                         [c (in-range (+ (obj-c1 obj) 1) (obj-c2 obj))])
                               (at g r c)))))))
      (for*/fold ([acc out])
                 ([r (in-range (+ (obj-r1 obj) 1) (obj-r2 obj))]
                  [c (in-range (+ (obj-c1 obj) 1) (obj-c2 obj))])
        (set-cell acc r c seed)))))