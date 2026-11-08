(rule!
  (let* ((objs (objects g 0))
         (source (pick-max objs obj-size))
         (key (obj-size source))
         (wrong-key (+ key 1))
         (source-color (obj-color source))
         (relay-colors
          (filter (lambda (color)
                    (and (not (= color source-color))
                         (= (count-color g color) wrong-key)))
                  (grid-colors g 0)))
         (relay-color (first relay-colors))
         (relay-grid
          (grid-from-fn (rows g) (cols g)
                        (lambda (r c)
                          (if (= (at g r c) relay-color)
                              relay-color
                              0)))))
    (crop-to-content relay-grid 0)))
