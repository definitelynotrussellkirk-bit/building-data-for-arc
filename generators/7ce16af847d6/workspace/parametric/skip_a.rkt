(rule!
  (let ((targets
         (sort (filter (lambda (o) (= (obj-color o) 3)) (objects g 0))
               (lambda (a b)
                 (or (< (obj-r1 a) (obj-r1 b))
                     (and (= (obj-r1 a) (obj-r1 b))
                          (< (obj-c1 a) (obj-c1 b))))))))
    (for/fold ([out g]) ([i (in-range (max 0 (- (length targets) 1)))])
      (let* ((a (list-ref targets i))
             (b (list-ref targets (+ i 1)))
             (pa (obj-center a))
             (pb (obj-center b))
             (bend (list (first pa) (second pb))))
        (paint-line (paint-line out pa bend 3) bend pb 3)))))
