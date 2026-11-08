(rule!
 (let ()
   (define matches
     (grid-from-fn (- (rows g) 1) (- (cols g) 1)
       (lambda (r c)
         (let ((left (at g (+ r 1) 0)) (top (at g 0 (+ c 1))))
           (if (= left top) left 0)))))
   (define parts (objects matches 0))
   (define largest (if (null? parts) 0 (apply max (map obj-size parts))))
   (for/fold ((out (grid-from-fn (rows matches) (cols matches) (lambda (r c) 0))))
             ((obj (in-list parts)))
     (if (= (obj-size obj) largest)
         (paint-cells out (obj-cells obj) (obj-color obj))
         out))))
