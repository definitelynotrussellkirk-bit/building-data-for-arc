(rule!
  (let* ([gc (first (filter (lambda (c)
                              (all? (lambda (r) (= (at g r c) 9))
                                    (range 0 (rows g))))
                            (range 0 (cols g))))]
         [stage
          (for*/fold ([out g])
                     ([r (in-range (rows g))]
                      [c (in-range gc)])
            (let ([v (at g r c)] [mc (- (* 2 gc) c)])
              (if (and (not (= v 0))
                       (not (= v 9))
                       (in-bounds? r mc (rows g) (cols g)))
                  (set-cell out r mc v)
                  out)))]
         [right-objs
          (filter (lambda (obj)
                    (and (not (= (obj-color obj) 9))
                         (> (second (obj-bbox obj)) gc)))
                  (objects stage 0))])
    (for/fold ([out stage])
              ([obj (in-list right-objs)])
      (for/fold ([acc out])
                ([p (in-list (obj-cells obj))])
        (set-cell acc (first p) (second p) (obj-size obj))))))
