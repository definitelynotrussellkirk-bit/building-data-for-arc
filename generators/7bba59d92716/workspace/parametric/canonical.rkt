(rule!
  (for/fold ([out g]) ([obj (filter (lambda (o) (and (= (obj-color o) 1) (= (obj-c1 o) (obj-c2 o)) (= (obj-size o) 5))) (objects g 0))])
    (set-cell out (quotient (+ (obj-r1 obj) (obj-r2 obj)) 2) (obj-c1 obj) 2)))