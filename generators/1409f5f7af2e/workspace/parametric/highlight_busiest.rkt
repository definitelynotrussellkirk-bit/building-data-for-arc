(rule!
  (lambda (g)
    (let* ((stage-a
             (grid-from-fn (rows g) (cols g)
               (lambda (r c)
                 (if (and (> r 0)
                          (< r (- (rows g) 1))
                          (= (at g r c) 0)
                          (= (at g (- r 1) c) 3)
                          (= (at g (+ r 1) c) 3))
                     2
                     (at g r c)))))
           (red-counts
             (for/list ((c (range 0 (cols stage-a))))
               (count-where (lambda (r) (= (at stage-a r c) 2))
                            (range 0 (rows stage-a)))))
           (best-count (apply max red-counts))
           (best-col
             (first
               (filter (lambda (c) (= (nth red-counts c) best-count))
                       (range 0 (cols stage-a))))))
      (grid-from-fn (rows stage-a) (cols stage-a)
        (lambda (r c)
          (if (and (= c best-col) (= (at stage-a r c) 3))
              1
              (at stage-a r c)))))))
