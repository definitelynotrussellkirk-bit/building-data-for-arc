(rule!
  (let* ((mask (grid-from-fn (rows g) (cols g)
                 (lambda (r c) (if (= (at g r c) 0) 0 1))))
         (objs (sort (objects mask 0)
                     (lambda (a b)
                       (cond [(not (= (obj-size a) (obj-size b))) (> (obj-size a) (obj-size b))]
                             [(not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b))]
                             [else (< (obj-c1 a) (obj-c1 b))]))))
         (chosen (first objs)))
    (subgrid g (obj-r1 chosen) (obj-c1 chosen) (obj-r2 chosen) (obj-c2 chosen))))