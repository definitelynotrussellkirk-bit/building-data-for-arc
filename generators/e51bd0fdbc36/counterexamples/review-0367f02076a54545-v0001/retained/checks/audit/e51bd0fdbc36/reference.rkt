(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((dr-dc (cond
                           ((let loop
                                 ((c 0))
                                 (cond
                                   ((>= c w) #t)
                                   ((= (at g 0 c) 9) (loop (+ c 1)))
                                   (else #f))) (list -1 0))
                           ((let loop
                                 ((c 0))
                                 (cond
                                   ((>= c w) #t)
                                   ((= (at g (- h 1) c) 9) (loop (+ c 1)))
                                   (else #f))) (list 1 0))
                           ((let loop
                                 ((r 0))
                                 (cond
                                   ((>= r h) #t)
                                   ((= (at g r 0) 9) (loop (+ r 1)))
                                   (else #f))) (list 0 -1))
                           (else (list 0 1))))
                  (dr (first dr-dc))
                  (dc (second dr-dc))
                  (all-nbrs-red-or-8 (lambda (r c)
                                       (let loop
                                            ((nbrs (list (list (- r 1) c)
                                                         (list (+ r 1) c)
                                                         (list r (- c 1))
                                                         (list r (+ c 1)))) (has-nbr #f))
                                            (cond
                                              ((null? nbrs) has-nbr)
                                              (else (let* ((n (car nbrs))
                                                           (nr (first n))
                                                           (nc (second n)))
                                                      (cond
                                                        ((or
                                                           (< nr 0)
                                                           (>= nr h)
                                                           (< nc 0)
                                                           (>= nc w)) (loop (cdr nbrs) has-nbr))
                                                        (else (let ((v (at g nr nc)))
                                                                (and
                                                                  (or (= v 2) (= v 8))
                                                                  (loop (cdr nbrs) #t))))))))))))
             (for*/fold ((out g))
                        ((r (range 0 h)) (c (range 0 w)))
                        (cond
                          ((!= (at g r c) 8) out)
                          ((all-nbrs-red-or-8 r c) (set-cell out r c 2))
                          (else (let ((nr (+ r dr))
                                      (nc (+ c dc)))
                                  (if (and (>= nr 0) (< nr h) (>= nc 0) (< nc w))
                                      (set-cell out nr nc 8)
                                      out)))))))))
