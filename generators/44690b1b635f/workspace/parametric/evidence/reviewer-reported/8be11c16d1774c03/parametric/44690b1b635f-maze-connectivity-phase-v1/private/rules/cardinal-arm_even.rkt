(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define marker-cells (positions-of g (lambda (v) (and (!= v 0) (!= v 8)))))
             (define marker-colors
               (remove-duplicates (map (lambda (p) (at g (first p) (second p)))
                                       marker-cells)))
             (define (color-count col)
               (count-if (lambda (p) (= (at g (first p) (second p)) col)) marker-cells))
             (define center-color
               (find-first (lambda (col) (= (color-count col) 1)) marker-colors))
             (define arm-color
               (find-first (lambda (col) (!= col center-color)) marker-colors))
             (define start (first (positions-of g (lambda (v) (= v center-color)))))
             (define (seen-pos? r c seen)
               (for/or ((e seen)) (and (= (first e) r) (= (second e) c))))
             (define visited
               (let loop
                    ((frontier (list (list (first start) (second start) 0))) (seen (list (list (first start) (second start) 0))))
                    (if (empty? frontier)
                        seen
                        (let* ((e (first frontier))
                               (r (first e))
                               (c (second e))
                               (d (third e))
                               (new (filter identity
                                            (map (lambda (delta)
                                                   (let ((nr (+ r (first delta)))
                                                         (nc (+ c (second delta))))
                                                     (and
                                                       (and
                                                         (in-bounds? nr nc h w)
                                                         (!= (at g nr nc) 8)
                                                         (not (seen-pos? nr nc seen)))
                                                       (list nr nc (+ d 1)))))
                                                 cardinal-deltas))))
                          (loop (append (rest frontier) new) (append seen new))))))
             (define (entry-at r c)
               (find-first (lambda (e) (and (= (first e) r) (= (second e) c))) visited))
             (cellmap g
                      (r c v)
                      (let ((e (entry-at r c)))
                        (if (and e (zero? v))
                            (if (zero? (modulo (third e) 2)) arm-color center-color)
                            v)))))))