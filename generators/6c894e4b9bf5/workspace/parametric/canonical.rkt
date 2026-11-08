(rule!
  (for/fold ([out g]) ([obj (filter (lambda (o) (and (= (obj-color o) 2) (= (obj-c1 o) (obj-c2 o)) (>= (obj-size o) 2))) (objects g 0))])
    (set-cell (set-cell out (obj-r1 obj) (obj-c1 obj) 1) (obj-r2 obj) (obj-c1 obj) 1)))