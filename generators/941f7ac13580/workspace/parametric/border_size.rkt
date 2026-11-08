(rule!
 (let* ((objs
         (sort (objects g 0)
               (lambda (a b)
                 (if (= (obj-r1 a) (obj-r1 b))
                     (< (obj-c1 a) (obj-c1 b))
                     (< (obj-r1 a) (obj-r1 b))))))
        (border-objects
         (filter
          (lambda (obj)
            (any? (lambda (p)
                    (or (= (first p) 0)
                        (= (second p) 0)
                        (= (first p) (- (rows g) 1))
                        (= (second p) (- (cols g) 1))))
                  (obj-cells obj)))
          objs))
        (anchor (first border-objects))
        (sizes (map obj-size objs))
        (offset (modulo (obj-size anchor) (length objs))))
   (grid (append (drop sizes offset) (take sizes offset)))))
