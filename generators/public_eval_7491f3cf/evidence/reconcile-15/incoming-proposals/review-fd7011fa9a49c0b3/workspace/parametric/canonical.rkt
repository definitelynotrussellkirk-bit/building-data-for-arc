(rule!
 ;; Four equal panels are separated by the uniform border color.  In panel one,
 ;; the large guide component is a wall and the single isolated guide cell marks
 ;; one of the wall's four-neighbor regions.  Copy panel two into that marked
 ;; region and panel three into every other region.  On guide-wall cells both
 ;; sources are eligible and panel two has priority.  Write the composition into
 ;; panel four while preserving the frame and the first three panels.
 (lambda (g)
  (let ()
   (define marker-panel 'second)
   (define h (rows g))
   (define w (cols g))
   (define border (at g 0 0))
   (define (runs indices)
    (if (null? indices) '()
     (let loop ([remaining (rest indices)] [start (first indices)]
                [previous (first indices)] [answer '()])
      (cond
       [(null? remaining) (reverse (cons (list start previous) answer))]
       [(= (first remaining) (+ previous 1))
        (loop (rest remaining) start (first remaining) answer)]
       [else
        (loop (rest remaining) (first remaining) (first remaining)
              (cons (list start previous) answer))]))))
   (define active-rows
    (for/list ([r (range h)]
               #:when (for/or ([c (range w)]) (not (= (at g r c) border)))) r))
   (define active-cols
    (for/list ([c (range w)]
               #:when (for/or ([r (range h)]) (not (= (at g r c) border)))) c))
   (define row-runs (runs active-rows))
   (define col-runs (runs active-cols))
   (define boxes
    (for*/list ([rr row-runs] [cc col-runs])
     (list (first rr) (first cc) (+ 1 (- (second rr) (first rr)))
           (+ 1 (- (second cc) (first cc))))))
   (define p1 (first boxes))
   (define p2 (second boxes))
   (define p3 (third boxes))
   (define p4 (fourth boxes))
   (define ph (third p1))
   (define pw (fourth p1))
   (define bg (at g (first p4) (second p4)))
   (define (panel-at box r c) (at g (+ (first box) r) (+ (second box) c)))
   (define local-positions (for*/list ([r (range ph)] [c (range pw)]) (list r c)))
   (define guide
    (filter (lambda (p) (not (= (panel-at p1 (first p) (second p)) bg))) local-positions))
   (define (near8? a b)
    (and (<= (abs (- (first a) (first b))) 1)
         (<= (abs (- (second a) (second b))) 1)
         (not (equal? a b))))
   (define marker
    (first (filter (lambda (p) (not (ormap (lambda (q) (near8? p q)) guide))) guide)))
   (define wall (filter (lambda (p) (not (equal? p marker))) guide))
   ;; A: flood the input-dependent marker-side region without crossing the wall.
   (define marker-region
    (let bfs ([front (list marker)] [back '()] [seen (list marker)])
     (cond
      [(null? front) (if (null? back) seen (bfs (reverse back) '() seen))]
      [else
       (define p (first front))
       (define next
        (filter (lambda (q)
                 (and (in-bounds? (first q) (second q) ph pw)
                      (not (member q wall)) (not (member q seen))))
         (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d))))
              cardinal-deltas)))
       (bfs (rest front) (append (reverse next) back) (append next seen))])))
   (define marked-box (if (equal? marker-panel 'second) p2 p3))
   (define other-box (if (equal? marker-panel 'second) p3 p2))
   ;; B consumes the flooded region to choose a source panel at every cell.
   (for/fold ([out g]) ([p local-positions])
    (define r (first p))
    (define c (second p))
    (define marked (panel-at marked-box r c))
    (define other (panel-at other-box r c))
    (define value
     (cond
      [(member p wall) (if (not (= marked bg)) marked other)]
      [(member p marker-region) marked]
      [else other]))
    (set-cell out (+ (first p4) r) (+ (second p4) c) value)))))
