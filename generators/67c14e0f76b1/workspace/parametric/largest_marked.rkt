(rule!
 (let* ((intermediate
         (fold-cells g g
          (lambda (out r c v)
           (if (and (= v 0)
                    (> c 0)
                    (< c (- w 1))
                    (= (at g r (- c 1)) 1)
                    (= (at g r (+ c 1)) 1))
               (set-cell out r c 2)
               out))))
        (marked
         (filter (lambda (obj) (= (obj-color obj) 2))
                 (objects intermediate 0)))
        (selected (pick-max marked obj-size)))
  (recolor-cells intermediate (obj-cells selected) 8)))
