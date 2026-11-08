(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define (in-b r c) (and (>= r 0) (< r h) (>= c 0) (< c w)))
             (define ones (find-color g 1))
             (define p1 (first ones))
             (define p2
               (find (lambda (p)
                       (and
                         (!= p p1)
                         (= 1 (abs (- (first p) (first p1))))
                         (= 1 (abs (- (second p) (second p1))))))
                     ones))
             (define dir
               (if p2
                   (list (- (first p2) (first p1)) (- (second p2) (second p1)))
                   (list 1 1)))
             (define (wall-orient r c)
               (let ((up (and (in-b (- r 1) c) (= (at g (- r 1) c) 2)))
                     (dn (and (in-b (+ r 1) c) (= (at g (+ r 1) c) 2))))
                 (if (or up dn) 'vertical 'horizontal)))
             (define max-steps (* h w 4))
             (define (walk gg r c dr dc fuel)
               (if (<= fuel 0)
                   gg
                   (let ((nr (+ r dr))
                         (nc (+ c dc)))
                     (cond
                       ((not (in-b nr nc)) gg)
                       ((= (at g nr nc) 2) (let* ((orient (wall-orient nr nc))
                                (ndr (if (= orient 'horizontal) (- dr) dr))
                                (ndc (if (= orient 'vertical) (- dc) dc)))
                           (walk gg r c ndr ndc (- fuel 1))))
                       (else (walk (set-cell gg nr nc 1) nr nc dr dc (- fuel 1)))))))
             (define sorted-by-row (sort-by ones (lambda (p) (first p))))
             (define start-bwd (first sorted-by-row))
             (define start-fwd (nth sorted-by-row (- (length sorted-by-row) 1)))
             (define after-fwd
               (walk g
                     (first start-fwd)
                     (second start-fwd)
                     (first dir)
                     (second dir)
                     max-steps))
             (walk after-fwd
                   (first start-bwd)
                   (second start-bwd)
                   (- 0 (first dir))
                   (- 0 (second dir))
                   max-steps)))))