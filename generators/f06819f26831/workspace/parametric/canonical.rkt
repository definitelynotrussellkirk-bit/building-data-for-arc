(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((mcomps (objects-multicolor g 0))
                  (templates (filter (lambda (o)
                                       (let ((colors (remove-duplicates (map (lambda (c)
                                                                               (at g
                                                                                   (first c)
                                                                                   (second c)))
                                                                             (obj-cells o)))))
                                         (>= (length colors) 2)))
                                     mcomps))
                  (tmpl-rels (map (lambda (t)
                                    (let* ((cells (obj-cells t))
                                           (bb (bbox-of-cells cells))
                                           (r1 (first bb))
                                           (c1 (second bb)))
                                      (map (lambda (c)
                                             (list (- (first c) r1)
                                                   (- (second c) c1)
                                                   (at g (first c) (second c))))
                                           cells)))
                                  templates))
                  (tmpl-set (make-hash))
                  (_1 (for ((t templates))
                        (for ((c (obj-cells t)))
                          (hash-set! tmpl-set (list (first c) (second c)) #t))))
                  (partials (reverse (fold-cells g
                                                 (list)
                                                 (lambda (acc r c v)
                                                   (if (and
                                                         (!= v 0)
                                                         (not (hash-has-key? tmpl-set
                                                                             (list r c))))
                                                       (cons (list r c v) acc)
                                                       acc)))))
                  (partial-set (make-hash))
                  (_2 (for ((p partials))
                        (hash-set! partial-set (list (first p) (second p)) (third p))))
                  (candidates (apply append
                                     (map (lambda (p)
                                            (apply append
                                                   (map (lambda (t-rel)
                                                          (map (lambda (tc)
                                                                 (list (- (first p)
                                                                          (first tc))
                                                                       (- (second p)
                                                                          (second tc))
                                                                       t-rel))
                                                               (filter (lambda (tc)
                                                                         (= (third tc)
                                                                            (third p)))
                                                                       t-rel)))
                                                        tmpl-rels)))
                                          partials)))
                  (scored (filter (lambda (x) x)
                                  (map (lambda (cand)
                                         (let* ((off-r (first cand))
                                                (off-c (second cand))
                                                (t-rel (third cand))
                                                (abs-cells (map (lambda (tc)
                                                                  (list (+ (first tc)
                                                                           off-r)
                                                                        (+ (second tc)
                                                                           off-c)
                                                                        (third tc)))
                                                                t-rel))
                                                (valid (let check
                                                            ((cs abs-cells))
                                                            (cond
                                                              ((null? cs) #t)
                                                              (else (let* ((c (car cs))
                                                                           (ar (first c))
                                                                           (ac (second c))
                                                                           (av (third c)))
                                                                      (cond
                                                                        ((not (in-bounds? ar
                                                                                          ac
                                                                                          h
                                                                                          w)) #f)
                                                                        ((hash-has-key? tmpl-set
                                                                                        (list ar
                                                                                              ac)) #f)
                                                                        ((let ((gv (at g
                                                                                       ar
                                                                                       ac)))
                                                                           (or
                                                                             (zero? gv)
                                                                             (= gv av))) (check (cdr cs)))
                                                                        (else #f)))))))
                                                (covered (if valid
                                                             (filter (lambda (ac)
                                                                       (hash-has-key? partial-set
                                                                                      (list (first ac)
                                                                                            (second ac))))
                                                                     abs-cells)
                                                             '
                                                             ())))
                                           (and
                                             (and valid (> (length covered) 0))
                                             (list (length covered) covered abs-cells))))
                                       candidates)))
                  (sorted (sort scored (lambda (a b) (> (first a) (first b)))))
                  (used (make-hash)))
             (for/fold ((out g))
               ((c sorted))
               (let* ((covered (second c))
                      (abs-cells (third c))
                      (overlap (let check
                                    ((cs covered))
                                    (cond
                                      ((null? cs) #f)
                                      ((hash-has-key? used
                                                      (list (first (car cs))
                                                            (second (car cs)))) #t)
                                      (else (check (cdr cs)))))))
                 (cond
                   (overlap out)
                   (else (for ((cov covered))
                           (hash-set! used (list (first cov) (second cov)) #t))
                         (paint-cells out abs-cells)))))))))