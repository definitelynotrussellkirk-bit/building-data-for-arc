(rule!
 (let* ((blue
         (filter (lambda (obj) (= (obj-color obj) 1))
                 (objects g 0)))
        (selected (pick-max blue obj-size))
        (wrong-input (recolor-cells g (obj-cells selected) 8)))
  (fold-cells wrong-input wrong-input
   (lambda (out r c v)
    (if (and (= v 0)
             (> c 0)
             (< c (- w 1))
             (= (at wrong-input r (- c 1)) 1)
             (= (at wrong-input r (+ c 1)) 1))
        (set-cell out r c 2)
        out)))))
