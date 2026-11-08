(rule!
 ;; Four equally sized panels share a uniform frame. The first panel contains
 ;; an eight-connected dividing path and a separate singleton of the same color.
 ;; Flood the four-connected open region containing the singleton, treating the
 ;; singleton itself as background. Copy source panel two into this region, and source panel three elsewhere. On the dividing path both
 ;; source patterns contribute: source two has priority where both have ink.
 ;; Only panel four changes; background source cells are transparent on the path.
 (lambda (g)
  (let ()
   (define frame (at g 0 0))
   (define active-rows (filter (lambda (r) (for/or ((c (range w))) (not (= (at g r c) frame)))) (range h)))
   (define active-cols (filter (lambda (c) (for/or ((r (range h))) (not (= (at g r c) frame)))) (range w)))
   (define starts (filter (lambda (c) (not (member (- c 1) active-cols))) active-cols))
   (define ends (filter (lambda (c) (not (member (+ c 1) active-cols))) active-cols))
   (define top (apply min active-rows))
   (define bottom (apply max active-rows))
   (define panels (for/list ((lo starts) (hi ends)) (subgrid g top lo bottom hi)))
   (define selector (first panels))
   (define source-two (third panels))
   (define source-three (second panels))
   (define background (at (fourth panels) 0 0))
   (define parts (objects-8 selector background))
   (define boundary (obj-cells (pick-max parts obj-size)))
   (define marker (first (obj-cells (pick-min parts obj-size))))
   (define ph (rows selector))
   (define pw (cols selector))
   (define mask (grid-from-fn ph pw (lambda (r c) (if (member (list r c) boundary) 1 0))))
   (define selected (flood-fill mask (first marker) (second marker) 2))
   (for*/fold ((out g)) ((r (range ph)) (c (range pw)))
    (set-cell out (+ top r) (+ (fourth starts) c)
     (cond ((= (at mask r c) 1)
            (if (= (at source-two r c) background) (at source-three r c) (at source-two r c)))
           ((= (at selected r c) 2) (at source-two r c))
           (else (at source-three r c))))))))
