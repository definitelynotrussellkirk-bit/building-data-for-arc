(rule!
  (let* ([rulers
          (filter
           (lambda (obj)
             (and (= (obj-color obj) 7)
                  (= (obj-c1 obj) (obj-c2 obj))
                  (>= (obj-size obj) 2)))
           (objects g 0))]
         [threshold (obj-size (first rulers))])
    (for/fold
     ([out g])
     ([obj
       (filter
        (lambda (candidate)
          (and (= (obj-color candidate) 2)
               (= (obj-c1 candidate) (obj-c2 candidate))
               (>= (obj-size candidate) threshold)))
        (objects g 0))])
      (set-cell
       (set-cell out (obj-r1 obj) (obj-c1 obj) 1)
       (obj-r2 obj) (obj-c1 obj) 1))))
