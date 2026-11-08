(rule!
  (for/fold ([out g]) ([obj (filter (lambda (o) (and (= (obj-color o) 3) (= (obj-r1 o) (obj-r2 o)))) (objects g 0))])
    (let ((r (obj-r1 obj)) (c (+ (obj-c2 obj) 1)))
      (if (and (< c (cols g)) (= (at g r c) 0))
          (set-cell out r c 2)
          out))))