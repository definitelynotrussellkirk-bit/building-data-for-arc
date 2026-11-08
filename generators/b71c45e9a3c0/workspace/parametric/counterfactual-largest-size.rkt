(rule!
  (let* ((greens
          (filter (lambda (obj) (= (obj-color obj) 3))
                  (objects g 0)))
         (largest
          (first
           (sort greens (lambda (a b) (> (obj-size a) (obj-size b))))))
         (target-size (obj-size largest)))
    (for/fold ((out g)) ((obj (in-list greens)))
      (if (= (obj-size obj) target-size)
          (let* ((bb (obj-bbox obj))
                 (key (at g (- (first bb) 1) (second bb))))
            (paint-cells out (obj-cells obj) key))
          out))))
