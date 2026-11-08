(rule!
  (let* ([gc (first (filter (lambda (c)
                              (all? (lambda (r) (= (at g r c) 9))
                                    (range 0 (rows g))))
                            (range 0 (cols g))))]
         [source-objs
          (filter (lambda (obj)
                    (and (not (= (obj-color obj) 9))
                         (< (second (obj-bbox obj)) gc)))
                  (objects g 0))])
    (for/fold ([out g])
              ([obj (in-list source-objs)])
      (for/fold ([acc out])
                ([p (in-list (obj-cells obj))])
        (let ([r (first p)] [mc (- (* 2 gc) (second p))])
          (if (in-bounds? r mc (rows g) (cols g))
              (set-cell acc r mc (obj-size obj))
              acc))))))
