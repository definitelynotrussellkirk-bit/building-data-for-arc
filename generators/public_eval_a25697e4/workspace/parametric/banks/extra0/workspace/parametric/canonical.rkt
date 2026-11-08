(rule!
 ;; Fit detached two-color keys into the missing cells of border locks.
 ;; A lock's cavity determines the whole key's rigid pose and handedness.
 ;; Move both colored parts together. A reflected fit exchanges their colors;
 ;; a pure rotation or translation preserves them. Source pieces are erased.
 ;; The admitted grammar has unique poses and disjoint one-to-one placements.
 (lambda (g)
  (let ()
   (define exchange-on-reflection #t)
   (define force-unreflected #f)
   (define bg (mode g -1))
   (define objs (objects-multicolor g bg))
   (define (colors o)
    (sort (remove-duplicates (map (lambda (p) (at g (first p) (second p))) (obj-cells o))) <))
   (define keys (filter (lambda (o) (= (length (colors o)) 2)) objs))
   (define mono (filter (lambda (o) (= (length (colors o)) 1)) objs))
   (define (side o)
    (cond ((= (obj-r1 o) 0) 0) ((= (obj-c2 o) (- w 1)) 1)
          ((= (obj-r2 o) (- h 1)) 2) ((= (obj-c1 o) 0) 3) (else -1)))
   (define lock-ids (remove-duplicates (map (lambda (o) (list (side o) (first (colors o)))) mono)))
   (define locks
    (for/list ((id lock-ids))
     (flatmap obj-cells (filter (lambda (o) (equal? id (list (side o) (first (colors o))))) mono))))
   (define stationary
    (for/fold ((out (empty-grid h w bg))) ((o mono))
     (paint-cells out (for/list ((p (obj-cells o))) (list (first p) (second p) (at g (first p) (second p)))))))
   (define (pose p turns flip)
    (let loop ((r (first p)) (c (if (= flip 1) (- (second p)) (second p))) (n turns))
     (if (= n 0) (list r c) (loop c (- r) (- n 1)))))
   (define (cavity lock)
    (let ((b (bbox-of-cells lock)))
     (filter (lambda (p) (not (member p lock))) (positions-in-rect (first b) (second b) (third b) (fourth b)))))
   (define (candidate key hole turns flip plug)
    (let* ((shifted (map (lambda (p) (append (pose p turns flip) (list (at g (first p) (second p))))) (obj-cells key)))
           (tip (filter (lambda (p) (= (third p) plug)) shifted))
           (tb (bbox-of-cells tip)) (hb (bbox-of-cells hole))
           (dr (- (first hb) (first tb))) (dc (- (second hb) (second tb)))
           (placed (map (lambda (p) (list (+ (first p) dr) (+ (second p) dc) (third p))) shifted))
           (tip-placed (map (lambda (p) (list (+ (first p) dr) (+ (second p) dc))) tip)))
     (if (and (equal? (sort tip-placed cell<) (sort hole cell<))
              (all? (lambda (p) (and (in-bounds? (first p) (second p) h w) (= (at stationary (first p) (second p)) bg))) placed))
         (list flip (colors key) placed) #f)))
   ;; Step A: the exact hole/plug fit supplies the pose and reflection bit.
   (define placements
    (for/list ((lock locks))
     (let* ((hole (cavity lock))
            (candidates (filter (lambda (x) x)
             (for*/list ((key keys) (flip (range 0 2)) (turns (range 0 4)) (plug (colors key)))
              (candidate key hole turns flip plug)))))
      (if (null? candidates) #f (first candidates)))))
   ;; Step B consumes the recovered placement, not a fixed direction or color.
   (for/fold ((out stationary)) ((item placements))
    (if (not item) out
     (let* ((flip (if force-unreflected 0 (first item)))
            (cs (second item)) (swap (and exchange-on-reflection (= flip 1))))
      (paint-cells out
       (map (lambda (p) (list (first p) (second p)
              (if swap (if (= (third p) (first cs)) (second cs) (first cs)) (third p))))
        (third item)))))))))
