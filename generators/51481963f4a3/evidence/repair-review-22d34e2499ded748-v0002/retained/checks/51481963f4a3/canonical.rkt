(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (objs (objects g 0))
                (templates (filter (lambda (o) (!= (obj-color o) 1)) objs))
                (ones (filter (lambda (o) (= (obj-color o) 1)) objs)))
           (paint-objects-by g
                             ones
                             (lambda (obj)
                               (let* ((hits (filter (lambda (t)
                                                      (cells-equal? (obj-cells obj)
                                                                    (obj-cells t)))
                                                    templates)))
                                 (if (null? hits) #f (obj-color (first hits)))))))))
