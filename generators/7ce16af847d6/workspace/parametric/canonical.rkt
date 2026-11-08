(rule!
  (for/fold ([out g]) ([obj (in-list (filter (lambda (o) (= (obj-color o) 1)) (objects g 0)))])
    (if (and (= (obj-size obj) 9) (= (obj-h obj) 3) (= (obj-w obj) 3))
        (paint-cells out (obj-cells obj) 3)
        out)))