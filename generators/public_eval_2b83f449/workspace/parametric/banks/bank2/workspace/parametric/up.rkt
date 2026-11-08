(rule!
 ;; Open each horizontal orange triple into two cyan side passages separated
 ;; by a vertical three-cell magenta pole. Treat original green markers as
 ;; traversable cyan while discovering the resulting four-connected paths.
 ;; Within each path, collect all markers at its upper endpoint, packed along
 ;; the path. Equal-height endpoints retain their initial markers. Empty
 ;; closed loops stay empty. The rule never relies on fixed stripe coordinates.
 (lambda (g)
   (let ()
     (define gates (filter (lambda (o) (= (obj-color o) 7)) (objects g 0)))
     (define cleared (recolor g 3 8))
     (define opened
       (for/fold ((out cleared)) ((o gates))
         (let ((r (obj-r1 o)) (c (+ (obj-c1 o) 1)))
           (recolor-cells (recolor-cells out (obj-cells o) 8)
             (list (list (- r 1) c) (list r c) (list (+ r 1) c)) 6))))
     (define route-grid opened)
     (define paths (filter (lambda (o) (= (obj-color o) 8)) (objects route-grid 0)))
     (define (neighbors cells p)
       (filter (lambda (q) (member q cells))
         (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) cardinal-deltas)))
     (define (walk cells current previous seen)
       (let ((next (filter (lambda (p) (and (not (equal? p previous)) (not (member p seen)))) (neighbors cells current))))
         (if (null? next) (list current)
           (cons current (walk cells (first next) current (cons current seen))))))
     (for/fold ((out opened)) ((o paths))
       (let* ((cells (obj-cells o))
              (markers (filter (lambda (p) (= (at g (first p) (second p)) 3)) cells))
              (ends (filter (lambda (p) (<= (length (neighbors cells p)) 1)) cells)))
         (if (null? markers) out
           (let ((dest
             (if (or (null? ends) (= (apply min (map first ends)) (apply max (map first ends))))
                 markers
                 (take (walk cells (pick-min ends first) #f '()) (length markers)))))
             (recolor-cells out dest 3))))))))
