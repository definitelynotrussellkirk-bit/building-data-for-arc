(rule!
  (lambda (g)
    (let* ((filled (fill-all-enclosed g 2))
           (enclosed-mask
             (map-grid g
               (lambda (r c value)
                 (if (and (= value 0) (= (cell-at filled r c) 2)) 1 0))))
           (eligible
             (filter (lambda (region) (>= (obj-size region) 32))
                     (objects enclosed-mask 0))))
      (paint-objects (recolor g 0 3) eligible 2))))