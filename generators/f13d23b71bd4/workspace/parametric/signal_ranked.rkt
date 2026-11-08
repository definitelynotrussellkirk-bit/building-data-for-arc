(rule!
 (lambda (g)
   (let* ((h (rows g))
          (w (cols g))
          (bg 7)
          (objs (objects g bg))
          (signal (first (filter (lambda (obj) (= (obj-color obj) 1)) objs)))
          (rank (obj-size signal))
          (candidates
           (filter
            (lambda (obj)
              (and (not (= (obj-color obj) 1))
                   (>= (obj-size obj) 4)))
            objs))
          (target (nth candidates (- rank 1))))
     (reduce
      (lambda (acc obj)
        (let* ((selected (equal? (obj-cells obj) (obj-cells target)))
               (drop (if selected (- (- h 1) (obj-r2 obj)) 0))
               (cells
                (map
                 (lambda (p) (list (+ (first p) drop) (second p)))
                 (obj-cells obj))))
          (paint-cells acc cells (obj-color obj))))
      (empty-grid h w bg)
      objs))))
