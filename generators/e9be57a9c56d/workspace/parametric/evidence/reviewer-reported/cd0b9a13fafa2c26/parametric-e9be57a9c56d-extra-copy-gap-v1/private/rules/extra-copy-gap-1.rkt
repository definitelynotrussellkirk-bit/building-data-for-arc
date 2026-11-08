(rule!
 ;; The largest object is a TEMPLATE; the loose dots (one shares its
 ;; color — the anchor) list stamp colors along a row or column. Stamp
 ;; one template copy per dot in that dot's color, chained from the
 ;; anchor edge-to-edge with the dots' own gaps as spacing.
 (lambda (g)
   (let ()
     (define objs (sort (objects-8 g 0)
                        (lambda (a b) (> (obj-size a) (obj-size b)))))
     (define template (first objs))
     (define t-r1 (obj-r1 template))
     (define t-c1 (obj-c1 template))
     (define t-h (obj-h template))
     (define t-w (obj-w template))
     (define pattern (normalize-cells (obj-cells template)))
     (define raw-ms  ;; (color r c) per dot
       (map (lambda (m)
              (let ((c (first (obj-cells m))))
                (list (obj-color m) (first c) (second c))))
            (rest objs)))
     (define horiz?
       (= 1 (length (remove-duplicates (map second raw-ms)))))
     (define ms
       (sort raw-ms (lambda (a b) (if horiz?
                                      (< (third a) (third b))
                                      (< (second a) (second b))))))
     (define n (length ms))
     (define anchor
       (find-first (lambda (i) (= (first (nth ms i))
                                  (obj-color template)))
                   (range 0 n)))
     (define (gap i j)
       (if horiz?
           (- (third (nth ms i)) (third (nth ms j)))
           (- (second (nth ms i)) (second (nth ms j)))))
     (define positions  ;; template corner per dot, chained from anchor
       (let ((fwd (let loop ((i (+ anchor 1)) (prev (list t-r1 t-c1))
                             (acc (list)))
                    (if (>= i n)
                        (reverse acc)
                        (let ((pos (if horiz?
                                       (list t-r1
                                             (+ (second prev) t-w -1
                                                (gap i (- i 1))
                                                1))
                                       (list (+ (first prev) t-h -1
                                                (gap i (- i 1))
                                                1)
                                             t-c1))))
                          (loop (+ i 1) pos (cons pos acc))))))
             (bwd (let loop ((i (- anchor 1)) (next (list t-r1 t-c1))
                             (acc (list)))
                    (if (< i 0)
                        acc
                        (let ((pos (if horiz?
                                       (list t-r1
                                             (+ (- (second next)
                                                   (gap (+ i 1) i)
                                                   t-w
                                                   1)
                                                1))
                                       (list (+ (- (first next)
                                                   (gap (+ i 1) i)
                                                   t-h
                                                   1)
                                                1)
                                             t-c1))))
                          (loop (- i 1) pos (cons pos acc)))))))
         (append bwd (list (list t-r1 t-c1)) fwd)))
     (for/fold ((out g)) ((i (range 0 n)))
       (if (= i anchor)
           out
           (paint-cells out
                        (map (lambda (p)
                               (list (+ (first (nth positions i))
                                        (first p))
                                     (+ (second (nth positions i))
                                        (second p))))
                             pattern)
                        (first (nth ms i))))))))