(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (result (make-hash))
                  (marked (make-hash)))
             (for* ((r (range 0 hh)) (c (range 0 ww)))
                   (hash-set! result (list r c) (at g r c)))
             (for* ((r1 (range 0 (- hh 3))) (c1 (range 0 (- ww 3))))
                   (unless
                     (hash-has-key? marked (list r1 c1))
                     (let* ((color (at g r1 c1))
                            (max-c c1))
                       (let wloop
                            ((mc c1))
                            (when
                              (and (< mc ww) (= (at g r1 mc) color))
                              (set! max-c mc)
                              (wloop (+ mc 1))))
                       (set! max-c (+ max-c 1))
                       (let* ((min-w (- max-c c1))
                              (best-r2 r1)
                              (best-c2 (- max-c 1))
                              (best-area 0))
                         (let rloop
                              ((r (+ r1 1)) (mw min-w))
                              (when
                                (< r hh)
                                (let cloop
                                     ((c c1) (row-w 0))
                                     (if (and (< c (+ c1 mw)) (= (at g r c) color))
                                         (cloop (+ c 1) (+ row-w 1))
                                         (let ((new-mw (min mw row-w)))
                                           (when
                                             (>= new-mw 4)
                                             (let ((area (* (+ 1 (- r r1)) new-mw)))
                                               (when
                                                 (and
                                                   (> area best-area)
                                                   (>= (+ 1 (- r r1)) 4))
                                                 (set! best-area area)
                                                 (set! best-r2 r)
                                                 (set! best-c2 (+ c1 new-mw -1))))
                                             (rloop (+ r 1) new-mw)))))))
                         (when
                           (and (>= (+ 1 (- best-r2 r1)) 4) (>= (+ 1 (- best-c2 c1)) 4))
                           (let ((solid #t))
                             (for* ((dr (range 0 (+ 1 (- best-r2 r1)))) (dc (range 0 (+ 1 (- best-c2 c1)))))
                                   (when
                                     (!= (at g (+ r1 dr) (+ c1 dc)) color)
                                     (set! solid #f)))
                             (when
                               (and solid (!= color 3))
                               (for* ((dr (range 0 (+ 1 (- best-r2 r1)))) (dc (range 0 (+ 1 (- best-c2 c1)))))
                                     (hash-set! result (list (+ r1 dr) (+ c1 dc)) 4)
                                     (hash-set! marked (list (+ r1 dr) (+ c1 dc)) #t)))))))))
             (build-grid hh ww (r c) (hash-ref result (list r c) 0))))))