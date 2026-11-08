(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (template (list))
                  (dummy-t (for* ((r (range 0 3)) (c (range 0 3)))
                                 (let ((v (at g r c)))
                                   (when
                                     (and (!= v 0) (!= v 5))
                                     (set! template (cons (list r c) template))))))
                  (t-rmin (min-of first template))
                  (t-cmin (min-of second template))
                  (t-norm (sort (map (lambda (p)
                                       (list (- (first p) t-rmin) (- (second p) t-cmin)))
                                     template)
                                (lambda (a b)
                                  (if (= (first a) (first b))
                                      (< (second a) (second b))
                                      (< (first a) (first b))))))
                  (visited (make-hash))
                  (objs (list))
                  (dummy-o (for* ((r (range 0 hh)) (c (range 0 ww)))
                                 (let ((v (at g r c)))
                                   (when
                                     (and
                                       (!= v 0)
                                       (!= v 5)
                                       (not (hash-has-key? visited (list r c))))
                                     (let ((comp (list))
                                           (oc v)
                                           (stack (list (list r c))))
                                       (let bfs
                                            ((stk stack))
                                            (unless
                                              (null? stk)
                                              (let* ((cur (car stk))
                                                     (rest (cdr stk))
                                                     (cr (first cur))
                                                     (cc (second cur)))
                                                (if (or
                                                      (< cr 0)
                                                      (>= cr hh)
                                                      (< cc 0)
                                                      (>= cc ww)
                                                      (!= (at g cr cc) oc)
                                                      (hash-has-key? visited
                                                                     (list cr cc)))
                                                    (bfs rest)
                                                    (begin
                                                      (hash-set! visited
                                                                 (list cr cc)
                                                                 #t)
                                                      (set! comp
                                                            (cons (list cr cc) comp))
                                                      (bfs (append (list (list (- cr 1)
                                                                               cc)
                                                                         (list (+ cr 1)
                                                                               cc)
                                                                         (list cr
                                                                               (- cc 1))
                                                                         (list cr
                                                                               (+ cc 1)))
                                                                   rest)))))))
                                       (set! objs (cons comp objs)))))))
                  (to-recolor #f)
                  (dummy-m (for ((obj objs))
                             (when
                               (and
                                 (not to-recolor)
                                 (not (for/or ((cell obj))
                                              (and
                                                (< (first cell) 3)
                                                (< (second cell) 3)))))
                               (let* ((o-rmin (min-of first obj))
                                      (o-cmin (min-of second obj))
                                      (o-norm (sort (map (lambda (p)
                                                           (list (- (first p) o-rmin)
                                                                 (- (second p) o-cmin)))
                                                         obj)
                                                    (lambda (a b)
                                                      (if (= (first a) (first b))
                                                          (< (second a) (second b))
                                                          (< (first a) (first b)))))))
                                 (when (equal? o-norm (let* ((rotated (map (lambda (p) (list (second p) (- 0 (first p)))) t-norm)) (rot-rmin (min-of first rotated)) (rot-cmin (min-of second rotated))) (sort (map (lambda (p) (list (- (first p) rot-rmin) (- (second p) rot-cmin))) rotated) (lambda (a b) (if (= (first a) (first b)) (< (second a) (second b)) (< (first a) (first b))))))) (set! to-recolor obj))))))
                  (recolor-set (make-hash))
                  (dummy-r (when
                             to-recolor
                             (for ((cell to-recolor)) (hash-set! recolor-set cell #t)))))
             (build-grid hh
                         ww
                         (r c)
                         (if (hash-has-key? recolor-set (list r c)) 5 (at g r c)))))))