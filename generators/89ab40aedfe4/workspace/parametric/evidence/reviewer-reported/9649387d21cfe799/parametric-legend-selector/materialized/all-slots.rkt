(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((fg (at g 0 0))
                  (starts (filter (lambda (c)
                                    (and
                                      (< (+ c 1) w)
                                      (= (at g 0 c) fg)
                                      (= (at g 0 (+ c 1)) fg)
                                      (or (zero? c) (zero? (at g 0 (- c 1))))))
                                  (range 0 w))))
             (define (col-count c)
               (count-if (lambda (r) (= (at g r (+ c 1)) fg)) (range 0 h)))
             (define ordered
               (sort starts
                     (lambda (a b)
                       (let ((ca (col-count a))
                             (cb (col-count b)))
                         (if (= ca cb) (< a b) (< ca cb))))))
             (define (copy-col acc dst src)
               (reduce (lambda (a r) (set-cell a r (+ dst 1) (at g r (+ src 1))))
                       acc
                       (range 0 h)))
             (let loop
                  ((acc g) (dsts starts) (srcs ordered))
                  (if (empty? dsts)
                      acc
                      (loop (copy-col acc (fst dsts) (fst srcs)) (cdr dsts) (cdr srcs))))))))
