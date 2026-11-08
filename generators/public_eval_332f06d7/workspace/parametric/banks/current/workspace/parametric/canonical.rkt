(rule!
 ;; Move the rigid black rectangle along blue cells toward the red goal.
 ;; Build a cell-distance field from red, then a separate graph of top-left
 ;; anchors whose ENTIRE footprint is walkable. Only anchors reachable by
 ;; cardinal unit translations from the original black block are eligible.
 ;; Minimize the sum of goal distances under the footprint; row-major breaks
 ;; ties. The originals all have unique optima. Preserve walls and unoccupied
 ;; red cells, restore the old black footprint to blue, and paint the endpoint.
 (lambda (g)
   (let ()
     (define halfway #f)
     (define deltas '((-1 0) (0 -1) (0 1) (1 0)))
     (define (neighbors p)
       (for/list ([d deltas]) (list (+ (first p) (first d)) (+ (second p) (second d)))))
     (define (flood starts allowed?)
       (let loop ([front starts]
                  [seen (for/fold ([acc (hash)]) ([p starts]) (hash-set acc p 0))]
                  [level 0])
         (define next
           (remove-duplicates
             (apply append
               (for/list ([p front])
                 (filter (lambda (q) (and (allowed? q) (not (hash-has-key? seen q))))
                         (neighbors p))))))
         (if (null? next) seen
             (loop next
                   (for/fold ([acc seen]) ([p next]) (hash-set acc p (+ level 1)))
                   (+ level 1)))))
     (define zeros (find-color g 0))
     (define goals (find-color g 2))
     (define top (apply min (map first zeros)))
     (define left (apply min (map second zeros)))
     (define sh (+ 1 (- (apply max (map first zeros)) top)))
     (define sw (+ 1 (- (apply max (map second zeros)) left)))
     (define start (list top left))
     (define (free? p)
       (member (safe-at g (first p) (second p) -1) '(0 1 2)))
     (define goal-distances (flood goals free?))
     (define legal
       (for*/fold ([acc (hash)]) ([r (range (+ 1 (- h sh)))] [c (range (+ 1 (- w sw)))])
         (if (for*/and ([a (range sh)] [b (range sw)])
               (member (at g (+ r a) (+ c b)) '(0 1 2)))
             (hash-set acc (list r c) #t) acc)))
     (define reachable (flood (list start) (lambda (p) (hash-has-key? legal p))))
     (define (position-key p) (+ (* (first p) w) (second p)))
     (define (score p)
       (for*/sum ([a (range sh)] [b (range sw)])
         (hash-ref goal-distances (list (+ (first p) a) (+ (second p) b)) (+ (* h w) 1))))
     (define terminal
       (pick-min (sort (hash-keys reachable) < #:key position-key) score))
     (define route
       (let trace ([p terminal] [path (list terminal)])
         (if (equal? p start) path
             (let ([previous
                    (pick-min
                      (filter (lambda (q)
                                (= (hash-ref reachable q -1) (- (hash-ref reachable p) 1)))
                              (neighbors p))
                      position-key)])
               (trace previous (cons previous path))))))
     (define destination (if halfway (list-ref route (quotient (length route) 2)) terminal))
     (define cleared (recolor-cells g zeros 1))
     (for*/fold ([out cleared]) ([a (range sh)] [b (range sw)])
       (set-cell out (+ (first destination) a) (+ (second destination) b) 0)))))
