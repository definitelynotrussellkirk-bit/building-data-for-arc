(rule!
  (let* ((objs (sort (objects g 0)
                     (lambda (a b)
                       (cond [(not (= (obj-size a) (obj-size b))) (> (obj-size a) (obj-size b))]
                             [else (< (obj-color a) (obj-color b))]))))
         (n (length objs))
         (selector (first
                    (filter (lambda (obj)
                              (or (= (obj-r1 obj) 0)
                                  (= (obj-c1 obj) 0)
                                  (= (obj-r2 obj) (- (rows g) 1))
                                  (= (obj-c2 obj) (- (cols g) 1))))
                            objs)))
         ;; Deliberately wrong intermediate: add one before reducing modulo n.
         (offset (modulo (+ (obj-size selector) 1) n))
         (ordered (append (drop objs offset) (take objs offset)))
         (total (+ (apply + (map obj-size ordered)) (max 0 (- n 1)))))
    (let pack ([remaining ordered] [left 0] [out (empty-grid 1 total 0)])
      (if (empty? remaining)
          out
          (let* ((obj (first remaining))
                 (next (for/fold ([acc out]) ([c (in-range left (+ left (obj-size obj)))])
                         (set-cell acc 0 c (obj-color obj)))))
            (pack (rest remaining) (+ left (obj-size obj) 1) next))))))
