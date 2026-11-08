(rule!
 ;; Crop the large radius-two-connected square tableau.  For every colour in
 ;; that square, count same-colour cue cells outside it and rotate that colour
 ;; layer clockwise by the count modulo four.  Layers rotate independently.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define points
    (filter (lambda (p) (not (= (at g (first p) (second p)) bg)))
            (grid-positions g)))
   (define (near2? a b)
    (and (<= (abs (- (first a) (first b))) 2)
         (<= (abs (- (second a) (second b))) 2)))
   (define (grow frontier remaining seen)
    (if (null? frontier)
        (list seen remaining)
        (let* ([p (first frontier)]
               [near (filter (lambda (q) (near2? p q)) remaining)]
               [left (filter (lambda (q) (not (member q near))) remaining)])
         (grow (append (rest frontier) near) left (append seen near)))))
   (define (components remaining)
    (if (null? remaining)
        '()
        (let* ([start (first remaining)]
               [grown (grow (list start) (rest remaining) (list start))])
         (cons (first grown) (components (second grown))))))
   (define main
    (first (sort (components points)
                 (lambda (a b) (> (length a) (length b))))))
   (define box (bbox-of-cells main))
   (define r0 (first box))
   (define c0 (second box))
   (define r1 (third box))
   (define c1 (fourth box))
   (define side (+ 1 (- r1 r0)))
   (define (inside? p)
    (and (<= r0 (first p) r1) (<= c0 (second p) c1)))
   (define inside-points (filter inside? points))
   (define colors
    (sort (remove-duplicates
           (map (lambda (p) (at g (first p) (second p))) inside-points)) <))
   (define direction -1)
   (define (turn-count color)
    (modulo (* direction
               (count-if (lambda (p)
                           (and (not (inside? p))
                                (= (at g (first p) (second p)) color)))
                         points))
            4))
   (define (rotate-one p)
    (list (second p) (- side 1 (first p))))
   (define (rotate-n p n)
    (if (= n 0) p (rotate-n (rotate-one p) (- n 1))))
   (define transformed
    (apply append
     (for/list ([color colors])
      (for/list ([p inside-points]
                 #:when (= (at g (first p) (second p)) color))
       (let ([q (rotate-n (list (- (first p) r0) (- (second p) c0))
                          (turn-count color))])
        (list (first q) (second q) color))))))
   (build-grid side side (r c)
    (let ([hits (filter (lambda (x) (and (= (first x) r) (= (second x) c)))
                        transformed)])
     (if (null? hits) bg (third (first hits))))))))
