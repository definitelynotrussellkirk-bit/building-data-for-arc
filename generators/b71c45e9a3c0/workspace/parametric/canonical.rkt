(rule!
 ;; Each green(3) object takes the color of the KEY cell sitting just above
 ;; its bbox top-left corner.
 (for/fold ((out g)) ((obj (in-list (filter (lambda (o) (= (obj-color o) 3))
                                            (objects g 0)))))
   (let* ((bb (obj-bbox obj))
          (key (at g (- (first bb) 1) (second bb))))
     (paint-cells out (obj-cells obj) key))))