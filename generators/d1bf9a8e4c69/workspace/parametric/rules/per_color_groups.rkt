(rule!
 (lambda (g)
   (let ()
     (define objs (objects g 0))
     (define colors (remove-duplicates (map obj-color objs)))
     (define (cells-for color)
       (apply append
              (map obj-cells
                   (filter (lambda (obj) (= (obj-color obj) color)) objs))))
     (define (corners-from-cells cells)
       (let* ((rs (map first cells)) (cs (map second cells))
              (r0 (min-list rs)) (c0 (min-list cs))
              (r1 (max-list rs)) (c1 (max-list cs)))
         (list (list r0 c0) (list r0 c1) (list r1 c0) (list r1 c1))))
     (define groups
       (map (lambda (color)
              (let ((cells (cells-for color)))
                (list color (corners-from-cells cells))))
            colors))
     (define corner-grid
       (for/fold ((out (empty-grid (rows g) (cols g) 0)))
                 ((group (in-list groups)))
         (paint-cells out (second group) (first group))))
     (define best
       (for*/fold ((best #f))
                  ((i (in-range (length groups)))
                   (j (in-range (+ i 1) (length groups)))
                   (p (in-list (second (list-ref groups i))))
                   (q (in-list (second (list-ref groups j)))))
         (let ((d (+ (abs (- (first p) (first q)))
                     (abs (- (second p) (second q))))))
           (if (or (not best) (< d (first best)))
               (list d p q)
               best))))
     (if (not best)
         corner-grid
         (let* ((p (second best)) (q (third best))
                (r0 (first p)) (c0 (second p))
                (r1 (first q)) (c1 (second q))
                (route
                 (append
                  (map (lambda (c) (list r0 c))
                       (range (min c0 c1) (+ (max c0 c1) 1)))
                  (map (lambda (r) (list r c1))
                       (range (min r0 r1) (+ (max r0 r1) 1)))))
                (open (filter (lambda (pos)
                                (= (at corner-grid (first pos) (second pos)) 0))
                              route)))
           (paint-cells corner-grid open 4))))))
