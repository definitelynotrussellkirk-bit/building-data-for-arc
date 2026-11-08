(rule!
 (lambda (g)
   (let* ((h (rows g))
          (w (cols g))
          (separator-rows
           (filter (lambda (r)
                     (andmap (lambda (c) (= (at g r c) (at g r 0))) (range w)))
                   (range h)))
          (separator (at g (first separator-rows) 0))
          (separator-cols
           (filter (lambda (c)
                     (andmap (lambda (r) (= (at g r c) separator)) (range h)))
                   (range w)))
          (tile-h (first separator-rows))
          (tile-w (first separator-cols))
          (tile-rows
           (filter (lambda (r)
                     (and (not (member r separator-rows))
                          (or (= r 0) (member (- r 1) separator-rows))))
                   (range h)))
          (tile-cols
           (filter (lambda (c)
                     (and (not (member c separator-cols))
                          (or (= c 0) (member (- c 1) separator-cols))))
                   (range w)))
          (tiles (for*/list ((tr tile-rows) (tc tile-cols))
                   (build-grid tile-h tile-w (r c) (at g (+ tr r) (+ tc c)))))
          (consensus
           (build-grid tile-h tile-w (r c)
             (mode-list (map (lambda (tile) (at tile r c)) tiles))))
          (background (mode consensus -1))
          (anomaly (first (filter (lambda (tile) (not (equal? tile consensus))) tiles)))
          (disagreements
           (for*/list ((r (range tile-h)) (c (range tile-w))
                       #:when (not (= (at consensus r c) (at anomaly r c))))
             (list r c)))
          (component-grid consensus)
          (components (objects component-grid background))
          (selected
           (filter (lambda (o)
                     (ormap (lambda (cell) (member cell disagreements)) (obj-cells o)))
                   components))
          (marked (apply append (map obj-cells selected))))
     (recolor-cells consensus marked 1))))
