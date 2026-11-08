(rule!
  (let* ((capped
           (for/fold ([out g])
                     ([obj (filter (lambda (o) (= (obj-r1 o) (obj-r2 o)))
                                   (objects g 0))])
             (let ((r (obj-r1 obj)) (c (+ (obj-c2 obj) 1)))
               (if (and (< c (cols g)) (= (at g r c) 0))
                   (set-cell out r c 2)
                   out))))
         (new-caps
           (filter-cells capped
             (lambda (r c v)
               (and (= v 2) (= (at g r c) 0))))))
    (cellmap capped
      (r c v)
      (if (= v 0)
          (let ((cap-rows
                  (map first
                       (filter (lambda (p) (= (second p) c)) new-caps))))
            (if (and (>= (length cap-rows) 2)
                     (> r (first cap-rows))
                     (< r (last cap-rows)))
                2
                v))
          v))))
