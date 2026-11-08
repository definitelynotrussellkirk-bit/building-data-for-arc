(rule!
 (let ()
   (define (rect-outline? obj)
     (and (>= (obj-h obj) 3)
          (>= (obj-w obj) 3)
          (= (obj-size obj) (- (* 2 (+ (obj-h obj) (obj-w obj))) 4))
          (all? (lambda (p)
                  (or (= (first p) (obj-r1 obj)) (= (first p) (obj-r2 obj))
                      (= (second p) (obj-c1 obj)) (= (second p) (obj-c2 obj))))
                (obj-cells obj))))
   (define selected
     (filter (lambda (obj) (and (= (obj-color obj) 3) (rect-outline? obj)))
             (objects g 0)))
   (define intermediate
     (for/fold ((out g)) ((obj (in-list selected)))
       (paint-cells out (obj-cells obj) 7)))
   (define barrier-mask (keep-only intermediate 7 0))
   (define filled-mask (fill-all-enclosed barrier-mask 2 0))
   (map-grid intermediate
     (lambda (r c value)
       (if (and (= value 0) (= (at filled-mask r c) 2)) 2 value)))))
