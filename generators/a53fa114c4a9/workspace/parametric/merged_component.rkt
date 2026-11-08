(rule! (let ((dummy 0))
  (let* ((mapping
           (filter values
             (for/list ((c (in-range (cols g))))
               (let ((s (at g 0 c)) (t (at g 1 c)))
                 (if (and (not (= s 0)) (not (= t 0))) (list s t) #f)))))
         (keep (filter (lambda (c) (= (at g 2 c) 1)) (range (cols g))))
         (body
           (for/list ((r (in-range 3 (rows g))))
             (for/list ((c (in-range (cols g))))
               (let* ((v (at g r c))
                      (hit (filter (lambda (p) (= (first p) v)) mapping)))
                 (if (empty? hit) v (second (first hit)))))))
         (ordered
           (sort (objects body 0)
                 (lambda (a b) (> (length (obj-cells a)) (length (obj-cells b))))))
         (winner-cells (if (empty? ordered) '() (obj-cells (first ordered))))
         (chosen
           (filter
             (lambda (c)
               (for/or ((p (in-list winner-cells))) (= (second p) c)))
             keep))
         (columns (if (empty? chosen) keep chosen)))
    (for/list ((r (in-range (rows body))))
      (for/list ((c (in-list columns))) (at body r c))))))
