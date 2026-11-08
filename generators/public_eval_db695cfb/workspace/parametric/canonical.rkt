(rule!
 ;; Blue cells are endpoints of one or more exact 45-degree signal segments.
 ;; Complete every such segment in blue. A red cell is active only when it lies
 ;; on a derived blue segment. Each active red cell emits a perpendicular red
 ;; beam through both canvas edges; red beams paint last.
 (lambda (g)
  (let ()
   (define beam-reach 'both_edges)
   (define background (mode g -1))
   (define positions (grid-positions g))
   (define blue (filter (lambda (p) (= (at g (first p) (second p)) 1)) positions))
   (define red (filter (lambda (p) (= (at g (first p) (second p)) 6)) positions))
   ;; A: derive complete diagonal paths and their signed orientations.
   (define segments
    (for*/list ([i (in-range (length blue))]
                [j (in-range (+ i 1) (length blue))]
                #:when
                (let* ([p (list-ref blue i)] [q (list-ref blue j)]
                       [dr (- (first q) (first p))]
                       [dc (- (second q) (second p))])
                 (and (> (abs dr) 0) (= (abs dr) (abs dc)))))
     (let* ([p (list-ref blue i)] [q (list-ref blue j)]
            [dr (- (first q) (first p))]
            [dc (- (second q) (second p))]
            [sr (if (> dr 0) 1 -1)]
            [sc (if (> dc 0) 1 -1)]
            [n (abs dr)]
            [cells (for/list ([k (in-range (+ n 1))])
                     (list (+ (first p) (* k sr)) (+ (second p) (* k sc))))])
       (list cells sr sc))))
   (define signal-cells (apply append (map first segments)))
   (define connected
    (paint-cells g
     (filter (lambda (p) (= (at g (first p) (second p)) background)) signal-cells)
     1))
   ;; B: membership in the derived paths gates red emission, and the stored
   ;; orientation determines the perpendicular forward direction. The episode
   ;; parameter decides whether that ray is mirrored through the trigger.
   (define beam-cells
    (apply append
     (for*/list ([p red] [segment segments]
                 #:when (member p (first segment)))
      (let* ([sr (second segment)] [sc (third segment)]
             [br sr] [bc (- sc)])
       (filter
        (lambda (q)
         (let ([dr (- (first q) (first p))] [dc (- (second q) (second p))])
          (and (= (* dr bc) (* dc br))
               (or (equal? beam-reach 'both_edges)
                   (>= (+ (* dr br) (* dc bc)) 0)))))
        positions)))))
   (paint-cells connected beam-cells 6))))
