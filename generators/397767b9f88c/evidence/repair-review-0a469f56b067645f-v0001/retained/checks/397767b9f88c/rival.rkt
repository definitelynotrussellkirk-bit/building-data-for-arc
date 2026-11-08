(rule!
  ;; Build the output grid
  (let* ((mask (grid-from-fn (rows g) (cols g)
                 (lambda (r c) (if (= (at g r c) 0) 0 1))))
         ;; Objects sorted by bbox position
         (objs (sort (objects mask 0)
                     (lambda (a b)
                       (if (= (obj-r1 a) (obj-r1 b))
                           (< (obj-c1 a) (obj-c1 b))
                           (< (obj-r1 a) (obj-r1 b))))))
         ;; Number of objects
         (n (length objs)))
    (grid-from-fn n n
      (lambda (r c)
        (if (let* ((transforms (all-transforms (obj-cells (nth objs r))))
                      (target (first (all-transforms (obj-cells (nth objs c))))))
                 (ormap (lambda (i) (equal? (list-ref transforms i) target))
                        '(0 1 2 3 4 6))) 2 0)))))