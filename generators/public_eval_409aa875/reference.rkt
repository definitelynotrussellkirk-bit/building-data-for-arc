(rule!
 ;; Every three-cell foreground object is a pointer.  A chevron points from the
 ;; midpoint of its two arms through its tip; an L points diagonally away from
 ;; its missing corner.  Move five cells in that direction.  Empty destinations
 ;; become maroon, coincident destinations become blue, and a hit recolours the
 ;; entire struck pointer maroon.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define objs
    (filter (lambda (o) (= (length (obj-cells o)) 3)) (objects-8 g bg)))
   (define travel 1)
   (define (diagonal? a b)
    (and (= (abs (- (first a) (first b))) 1)
         (= (abs (- (second a) (second b))) 1)))
   (define (cardinal? a b)
    (= (+ (abs (- (first a) (first b)))
          (abs (- (second a) (second b)))) 1))
   (define (pointer obj)
    (let* ([cells (obj-cells obj)]
           [tips
            (filter (lambda (p)
                      (= (length (filter (lambda (q)
                                           (and (not (equal? p q)) (diagonal? p q)))
                                         cells)) 2))
                    cells)])
     (if (not (null? tips))
         (let* ([tip (first tips)]
                [arms (filter (lambda (q) (not (equal? q tip))) cells)]
                [mr (quotient (+ (first (first arms)) (first (second arms))) 2)]
                [mc (quotient (+ (second (first arms)) (second (second arms))) 2)])
          (list tip (list (- (first tip) mr) (- (second tip) mc))))
         (let* ([elbows
                 (filter (lambda (p)
                           (= (length (filter (lambda (q)
                                              (and (not (equal? p q)) (cardinal? p q)))
                                            cells)) 2))
                         cells)]
                [elbow (first elbows)]
                [arms (filter (lambda (q) (not (equal? q elbow))) cells)]
                [dr (+ (- (first (first arms)) (first elbow))
                       (- (first (second arms)) (first elbow)))]
                [dc (+ (- (second (first arms)) (second elbow))
                       (- (second (second arms)) (second elbow)))])
          (list elbow (list (- dr) (- dc)))))))
   (define endpoints
    (filter (lambda (p) (in-bounds? (first p) (second p) (rows g) (cols g)))
     (for/list ([obj objs])
      (let* ([pd (pointer obj)] [origin (first pd)] [d (second pd)])
       (list (+ (first origin) (* 5 travel (first d)))
             (+ (second origin) (* 5 travel (second d))))))))
   (define hit-objs
    (filter (lambda (obj)
              (any? (lambda (p) (member p endpoints)) (obj-cells obj)))
            objs))
   (define hit-cells
    (if (null? hit-objs)
        '()
        (remove-duplicates (apply append (map obj-cells hit-objs)))))
   (build-grid (rows g) (cols g) (r c)
    (let* ([p (list r c)] [v (at g r c)]
           [n (count-if (lambda (q) (equal? p q)) endpoints)])
     (cond [(member p hit-cells) 9]
           [(not (= v bg)) v]
           [(>= n 2) 1]
           [(= n 1) 9]
           [else bg]))))))
