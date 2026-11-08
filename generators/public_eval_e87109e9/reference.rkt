(rule!
 ;; The six-row legend maps obstacle colors to left or right turns. A solid
 ;; color-8 square emits four square-width rays. Each ray advances through the
 ;; original scene; immediately before a colored obstacle it turns according to
 ;; that obstacle's legend command. Repeated position/direction states stop.
 ;; Remove the legend and paint traversed background cells color 8.
 (lambda (g)
  (let ()
   (define turn-policy 'legend)
   (define sh (- h 6))
   (define scene (build-grid sh w (r c) (at g (+ r 6) c)))
   (define border (at g 0 0))
   (define legend
    (for/list ((i (range (quotient w 6))))
     (let* ((base (* i 6))
            (colored
             (for*/list ((r (range 1 5)) (lc (range 1 5))
                         #:when (let ((v (at g r (+ base lc))))
                                  (and (not (= v 0)) (not (= v border)))))
              (list lc (at g r (+ base lc)))))
            (first-cell (first colored))
            (lc (first first-cell))
            (color (second first-cell)))
      (list color (if (<= lc 2) 'left 'right)))))
   (define bg (mode scene -1))
   (define seed
    (for*/list ((r (range sh)) (c (range w)) #:when (= (at scene r c) 8))
     (list r c)))
   (define r0 (apply min (map first seed)))
   (define r1 (apply max (map first seed)))
   (define c0 (apply min (map second seed)))
   (define c1 (apply max (map second seed)))
   (define size (+ 1 (- r1 r0)))
   (define (footprint r c)
    (for*/list ((rr (range r (+ r size))) (cc (range c (+ c size)))) (list rr cc)))
   (define (inside? r c)
    (and (<= 0 r) (<= 0 c) (<= (+ r size) sh) (<= (+ c size) w)))
   (define (command color)
    (let* ((named (second (assoc color legend)))
           (selected (if (eq? turn-policy 'legend) named
                         (if (eq? named 'left) 'right 'left))))
     selected))
   (define (turned dr dc side)
    (if (eq? side 'left) (list (- dc) dr) (list dc (- dr))))
   (define (walk r c dr dc seen)
    (define state (list r c dr dc))
    (if (member state seen) '()
     (let* ((here (footprint r c)) (nr (+ r dr)) (nc (+ c dc)))
      (if (not (inside? nr nc)) here
       (let ((hits
        (remove-duplicates
         (for/list ((p (footprint nr nc))
                    #:when (let ((v (at scene (first p) (second p))))
                             (and (not (= v bg)) (not (= v 8)))))
          (at scene (first p) (second p))))))
        (if (null? hits)
            (append here (walk nr nc dr dc (cons state seen)))
            (let* ((next (turned dr dc (command (first hits))))
                   (ndr (first next)) (ndc (second next)))
             (append here (walk r c ndr ndc (cons state seen))))))))))
   (define marks
    (remove-duplicates
     (apply append
      (for/list ((d '((-1 0) (1 0) (0 -1) (0 1))))
       (walk r0 c0 (first d) (second d) '())))))
   (build-grid sh w (r c)
    (if (and (= (at scene r c) bg) (member (list r c) marks)) 8 (at scene r c))))))
