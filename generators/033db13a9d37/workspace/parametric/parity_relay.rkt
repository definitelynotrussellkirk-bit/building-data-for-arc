(rule!
 (lambda (g)
   (let* ((markers
            (for*/list ((r (in-range (rows g))) (c (in-range (cols g)))
                        #:when (not (= (at g r c) 0)))
              (list r c (at g r c))))
          (origin (first markers))
          (lane-mask
            (map-grid g
              (lambda (r c value)
                (if (and (> r (first origin))
                         (= (remainder c 2) (remainder (second origin) 2))) 4 0))))
          (hits (filter (lambda (p) (= (at lane-mask (first p) (second p)) 4)) markers))
          (target (if (null? hits) origin (first hits)))
          (tr (first target)) (tc (second target)) (tv (third target)))
     (map-grid g
       (lambda (r c value)
         (cond
           ((and (= r (+ tr 1)) (= c tc)) tv)
           ((and (<= r tr) (= (remainder c 2) (remainder tc 2))) 4)
           (else 0)))))))
