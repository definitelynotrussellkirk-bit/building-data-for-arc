(rule!
 ;; Maroon cells are collected into the green box around the red marker.
 ;; Magenta 6 is an impassable wall; orange 7 is floor. Compute shortest
 ;; cardinal path distances from the marker, ignoring unreachable maroon cells.
 ;; Move the nearest reachable cells, up to the number of destination slots,
 ;; into the box in row-major order, including the red center slot. Vacated
 ;; sources become orange. Preserve excess, unreachable tokens, and all walls.
 ;; Distance ties use row-major order (an explicit totalization); generated
 ;; lessons avoid a tie at the capacity cutoff for either episode setting.
 (lambda (g)
  (let ()
   (define collection-order 'nearest)
   (define distance-mode 'geodesic)
   (define positions (grid-positions g))
   (define origin (first (filter (lambda (p) (= (at g (first p) (second p)) 2)) positions)))
   (define slots (filter (lambda (p) (member (at g (first p) (second p)) '(2 3))) positions))
   ;; A: two-list FIFO traversal builds an input-dependent immutable distance map.
   (define distance-map
    (let bfs ([front (list origin)] [back '()] [dist (hash origin 0)])
     (cond
      [(null? front) (if (null? back) dist (bfs (reverse back) '() dist))]
      [else
       (define p (first front))
       (define next
        (filter (lambda (q)
                  (and (in-bounds? (first q) (second q) (rows g) (cols g))
                       (not (= (at g (first q) (second q)) 6))
                       (not (hash-has-key? dist q))))
                (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) cardinal-deltas)))
       (define updated (for/fold ([result dist]) ([q next]) (hash-set result q (+ 1 (hash-ref dist p)))))
       (bfs (rest front) (append (reverse next) back) updated)])))
   (define candidates
    (for/list ([p positions]
               #:when (and (= (at g (first p) (second p)) 9)
                           (or (equal? distance-mode 'manhattan) (hash-has-key? distance-map p))))
     (list p (if (equal? distance-mode 'manhattan)
                 (+ (abs (- (first p) (first origin))) (abs (- (second p) (second origin))))
                 (hash-ref distance-map p)))))
   ;; B consumes reachability and distance; geometry cannot be ranked first.
   (define ranked
    (sort candidates
     (lambda (a b)
      (if (= (second a) (second b)) (cell< (first a) (first b))
       (if (equal? collection-order 'nearest) (< (second a) (second b)) (> (second a) (second b)))))))
   (define selected (take ranked (min (length slots) (length ranked))))
   (define erased (recolor-cells g (map first selected) 7))
   (recolor-cells erased (take slots (length selected)) 9))))
