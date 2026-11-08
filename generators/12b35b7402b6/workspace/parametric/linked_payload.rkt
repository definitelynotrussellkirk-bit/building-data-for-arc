(rule!
 ;; Stage A: canonical marker-count selection recolors the matching blue object red.
 ;; Stage B: recompute red 4-components on that intermediate; the unique largest
 ;; red component's size selects an azure object, which is recolored yellow.
 (let ((dummy 0))
   (define (objs-color grid color)
     (filter (lambda (obj) (= (obj-color obj) color)) (objects grid 0)))
   (define (paint-obj grid obj color)
     (paint-cells grid (obj-cells obj) color))
   (define (bbox< a b)
     (cond ((not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b)))
           ((not (= (obj-c1 a) (obj-c1 b))) (< (obj-c1 a) (obj-c1 b)))
           ((not (= (obj-r2 a) (obj-r2 b))) (< (obj-r2 a) (obj-r2 b)))
           (else (< (obj-c2 a) (obj-c2 b)))))
   (define (size-desc< a b)
     (if (= (obj-size a) (obj-size b))
         (bbox< a b)
         (> (obj-size a) (obj-size b))))
   (let* ((count5 (length (find-color g 5)))
          (blue-target
           (first (sort (filter (lambda (obj) (= (obj-size obj) count5))
                                (objs-color g 1))
                        bbox<)))
          (stage-a (paint-obj g blue-target 2))
          (red-key (first (sort (objs-color stage-a 2) size-desc<)))
          (key-size (obj-size red-key))
          (payload
           (first (sort (filter (lambda (obj) (= (obj-size obj) key-size))
                                (objs-color stage-a 8))
                        bbox<))))
     (paint-obj stage-a payload 4))))
