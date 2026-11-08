(rule!
  (let* ((all-objs (objects g 0))
         (colors (grid-colors g 0))
         (winners
          (map
           (lambda (color)
             (first
              (sort
               (filter (lambda (obj) (= (obj-color obj) color)) all-objs)
               (lambda (a b)
                 (if (= (obj-size a) (obj-size b))
                     (if (= (obj-r1 a) (obj-r1 b))
                         (< (obj-c1 a) (obj-c1 b))
                         (< (obj-r1 a) (obj-r1 b)))
                     (> (obj-size a) (obj-size b)))))))
           colors))
         (threshold
          (for/fold ([best (obj-size (first winners))])
                    ([winner (in-list (rest winners))])
            (min best (obj-size winner)))))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)])
              ([obj (in-list all-objs)])
      (if (>= (obj-size obj) threshold)
          (paint-cells out (obj-cells obj) (obj-color obj))
          out))))
