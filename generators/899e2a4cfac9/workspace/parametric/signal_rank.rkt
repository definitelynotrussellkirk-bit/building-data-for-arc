(rule!
  (let* ([h (rows g)]
         [w (cols g)]
         [objs (objects g 0)]
         [touches-border?
          (lambda (obj)
            (any? (lambda (p)
                    (or (= (first p) 0)
                        (= (first p) (- h 1))
                        (= (second p) 0)
                        (= (second p) (- w 1))))
                  (obj-cells obj)))]
         [signal
          (find-first (lambda (obj)
                        (and (= (obj-color obj) 1)
                             (touches-border? obj)))
                      objs)]
         [rank (obj-size signal)]
         [interiors (filter (lambda (obj) (not (touches-border? obj))) objs)]
         [chosen (list-ref interiors (- rank 1))])
    (paint-cells (empty-grid h w 0)
                 (obj-cells chosen)
                 (obj-color chosen))))