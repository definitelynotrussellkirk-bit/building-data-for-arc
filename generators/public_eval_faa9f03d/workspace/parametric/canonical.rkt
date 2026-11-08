(rule!
 ;; Repair uniquely colored orthogonal paths on black. Red cells mark path
 ;; vertices and reverse that path's observed over/under crossing relation.
 ;; Yellow cells point away from a pivot: replace its opposite terminal arm
 ;; with a straight extension toward the indicated edge. Recover topology
 ;; and crossing order BEFORE rerouting, so a new crossing inherits the order.
 ;; Axial runs and three alternating samples support missing cells; a gap
 ;; between two transverse runs alone does not establish a connecting edge.
 ;; Unobserved/cyclic crossing orders use a deterministic color-order fallback.
 (lambda (g)
  (let ()
   (define reverse-marked? #t)
   (define (v p) (safe-at g (first p) (second p) -1))
   (define (add p d) (list (+ (first p) (first d)) (+ (second p) (second d))))
   (define (mul d n) (list (* (first d) n) (* (second d) n)))
   (define (perp d) (list (list (second d) (first d)) (list (- (second d)) (- (first d)))))
   (define colors (filter (lambda (x) (not (member x '(0 2 4)))) (grid-colors g)))
   (define (recover color)
    (define (ok p) (or (= (v p) color) (= (v p) 2)))
    (define (support p d)
     (or (ok (add p d))
         (and (ok (add p (mul d 2)))
              (or (ok (add p (mul d 3))) (ok (add p (mul d 4)))))))
    (define (transverse p d) (for/or ((e (perp d))) (ok (add p e))))
    (define (corner p d)
     (or (= (v p) 2) (and (= (v p) color) (for/or ((e (perp d))) (support p e)))))
    (define (end p d)
     (if (corner p d) p
      (let walk ((q (add p d)) (last p))
       (cond ((= (v q) -1) last)
             ((and (ok q) (corner q d)) q)
             (else (walk (add q d) (if (ok q) q last)))))))
    (define segments
     (remove-duplicates
      (for*/list ((p (grid-positions g)) (d '((0 1) (1 0))) (distance '(1 2))
        #:when
        (let ((q (add p (mul d distance))))
         (and (ok p) (ok q) (or (= (v p) color) (= (v q) color))
              (or (= distance 1) (ok (add p (mul d -2))) (ok (add q (mul d 2))))
              (not (and (= distance 2) (transverse p d) (transverse q d))))))
       (let ((q (add p (mul d distance))))
        (list (end p (mul d -1)) (end q d))))))
    (define cells
     (remove-duplicates
      (append (find-color g color)
       (apply append
        (map (lambda (s)
               (positions-in-rect (first (first s)) (second (first s))
                                  (first (second s)) (second (second s)))) segments)))))
    (list color cells (for/or ((p cells)) (= (v p) 2))))
   (define paths (map recover colors))
   (define observed-over
    (filter (lambda (x) x)
     (for*/list ((i (range (length paths))) (j (range (+ i 1) (length paths))))
      (let* ((a (list-ref paths i)) (b (list-ref paths j))
             (overlap (filter (lambda (p) (member p (second b))) (second a)))
             (na (count-if (lambda (p) (= (v p) (first a))) overlap))
             (nb (count-if (lambda (p) (= (v p) (first b))) overlap)))
       (if (= (+ na nb) 0) #f
        (if (>= na nb) (list (first b) (first a)) (list (first a) (first b))))))))
   (define (record color) (for/first ((p paths) #:when (= (first p) color)) p))
   (define edges
    (map (lambda (edge)
           (if (and reverse-marked?
                    (or (third (record (first edge))) (third (record (second edge)))))
               (reverse edge) edge)) observed-over))
   (define paint-order
    (let loop ((pending colors) (done '()))
     (if (null? pending) (reverse done)
      (let ((next
             (or (for/first ((color pending)
                   #:when (not (for/or ((edge edges))
                     (and (= (second edge) color) (member (first edge) pending))))) color)
                 (first pending))))
       (loop (filter (lambda (x) (not (= x next))) pending) (cons next done))))))
   (define (route item)
    (define mask (second item))
    (define turns
     (for*/list ((q (find-color g 4)) (d cardinal-deltas)
       #:when (let ((pivot (add q (mul d -1))) (old (add q (mul d -2))))
        (and (member pivot mask) (member old mask) (not (member q mask))
             (for/or ((e (perp d))) (member (add pivot e) mask)))))
      (list (add q (mul d -1)) d)))
    (define (old-arm turn)
     (define pivot (first turn))
     (define initial (add pivot (mul (second turn) -1)))
     (let loop ((todo (list initial)) (seen (list pivot)) (found '()))
      (if (null? todo) found
       (let ((p (first todo)))
        (if (or (member p seen) (not (member p mask)))
            (loop (rest todo) seen found)
            (loop (append (map (lambda (d) (add p d)) cardinal-deltas) (rest todo))
                  (cons p seen) (cons p found)))))))
    (define removed (apply append (map old-arm turns)))
    (define added
     (apply append
      (map (lambda (turn)
             (let loop ((p (first turn)) (out '()))
              (if (in-bounds? (first p) (second p) h w)
                  (loop (add p (second turn)) (cons p out)) out))) turns)))
    (remove-duplicates (append (filter (lambda (p) (not (member p removed))) mask) added)))
   (for/fold ((out (build-grid h w (r c) 0))) ((color paint-order))
    (recolor-cells out (route (record color)) color)))))
