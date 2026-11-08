(rule!
 ;; Color-6 separator lines divide equal square panels on a color-7 field.
 ;; Every panel carries one unrotated path with one incoming and/or outgoing
 ;; boundary coordinate.  Match outgoing coordinates to incoming coordinates,
 ;; recover the unique complete chain, and lay its panels in chain order along
 ;; the connector axis.  Repeated connector coordinates are allowed: uniqueness
 ;; is global over the complete chain, not greedy at a single join.
 (lambda (g)
  (let ()
   (define traversal 'reverse)
   (define bg 7)
   (define sep 6)
   (define hh (rows g))
   (define ww (cols g))
   (define row-counts
    (for/list ([r (range hh)])
     (length (filter (lambda (c) (= (at g r c) sep)) (range ww)))))
   (define col-counts
    (for/list ([c (range ww)])
     (length (filter (lambda (r) (= (at g r c) sep)) (range hh)))))
   (define max-row (apply max row-counts))
   (define max-col (apply max col-counts))
   (define sep-rows
    (if (>= max-row max-col)
     (for/list ([r (range hh)] #:when (= (list-ref row-counts r) max-row)) r)
     '()))
   (define sep-cols
    (if (>= max-col max-row)
     (for/list ([c (range ww)] #:when (= (list-ref col-counts c) max-col)) c)
     '()))
   (define first-separators (append sep-rows sep-cols))
   (define side (apply min first-separators))
   (define nr (+ 1 (length sep-rows)))
   (define nc (+ 1 (length sep-cols)))
   (define panels
    (for*/list ([pr (range nr)] [pc (range nc)])
     (let ([r0 (* pr (+ side 1))] [c0 (* pc (+ side 1))])
      (subgrid g r0 c0 (+ r0 side -1) (+ c0 side -1)))))
   (define (edge-contact panel edge)
    (define values
     (cond
      [(equal? edge 'top)
       (for/list ([c (range side)] #:when (not (= (at panel 0 c) bg))) c)]
      [(equal? edge 'bottom)
       (for/list ([c (range side)] #:when (not (= (at panel (- side 1) c) bg))) c)]
      [(equal? edge 'left)
       (for/list ([r (range side)] #:when (not (= (at panel r 0) bg))) r)]
      [else
       (for/list ([r (range side)] #:when (not (= (at panel r (- side 1)) bg))) r)]))
    (if (null? values) #f (first values)))
   (define records
    (for/list ([panel panels])
     (list (edge-contact panel 'top) (edge-contact panel 'bottom)
           (edge-contact panel 'left) (edge-contact panel 'right))))
   (define vertical?
    (for/and ([rec records])
     (and (not (third rec)) (not (fourth rec))
          (or (first rec) (second rec)))))
   (define incoming-index (if vertical? 0 2))
   (define outgoing-index (if vertical? 1 3))
   (define (incoming i) (list-ref (list-ref records i) incoming-index))
   (define (outgoing i) (list-ref (list-ref records i) outgoing-index))
   (define indices (range (length panels)))
   (define starts
    (filter (lambda (i) (and (not (incoming i)) (outgoing i))) indices))
   (define ends
    (filter (lambda (i) (and (incoming i) (not (outgoing i)))) indices))
   (define start (first starts))
   (define finish (first ends))
   ;; Step A: derive the unique complete connector chain.  The DFS is necessary
   ;; for official examples where the same coordinate appears at every join.
   (define (extend path unused)
    (if (null? unused)
     (if (= (last path) finish) (list path) '())
     (let ([value (outgoing (last path))])
      (if (not value) '()
       (apply append
        (for/list ([i unused] #:when (equal? (incoming i) value))
         (extend (append path (list i)) (remove i unused))))))))
   (define solutions (extend (list start) (remove start indices)))
   (define order (first solutions))
   ;; Step B consumes that input-derived chain.  Reverse traversal rotates every
   ;; panel 180 degrees so its entry/exit coordinates still meet.
   (define ordered
    (if (equal? traversal 'forward)
     (map (lambda (i) (list-ref panels i)) order)
     (map rotate-180 (reverse (map (lambda (i) (list-ref panels i)) order)))))
   (define count (length ordered))
   (if vertical?
    (build-grid (+ (* count side) (- count 1)) side (r c)
     (let ([slot (quotient r (+ side 1))] [offset (modulo r (+ side 1))])
      (if (= offset side) sep (at (list-ref ordered slot) offset c))))
    (build-grid side (+ (* count side) (- count 1)) (r c)
     (let ([slot (quotient c (+ side 1))] [offset (modulo c (+ side 1))])
      (if (= offset side) sep (at (list-ref ordered slot) r offset))))))))
