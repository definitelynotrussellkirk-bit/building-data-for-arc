(rule!
 ;; Blue T glyphs point from a source region toward the first different region
 ;; on their ray. A nonblue center supplies the new ink; a blue center means
 ;; the original source ink. Restore the overwritten regions before routing,
 ;; freeze all destinations, and recolor simultaneously rather than cascading.
 ;; A five-cell burgundy top-corner glyph is erased and requests a quarter-turn:
 ;; a left corner turns clockwise; a right corner turns counterclockwise.
 (lambda (g)
  (let ()
   (define use-payload #t)
   (define dirs '((-1 0) (1 0) (0 -1) (0 1)))
   (define (value r c) (if (and (<= 0 r) (< r h) (<= 0 c) (< c w)) (at g r c) -1))
   (define arrows
    (filter (lambda (x) x)
     (for*/list ((r (range h)) (c (range w)))
      (let ((arms (filter (lambda (d) (= (value (+ r (first d)) (+ c (second d))) 1)) dirs)))
       (if (not (= (length arms) 3)) #f
        (let* ((missing (first (filter (lambda (d) (not (member d arms))) dirs)))
               (dr (- (first missing))) (dc (- (second missing)))
               (one (value (+ r dr dc) (+ c dc dr))) (two (value (+ r dr (- dc)) (+ c dc (- dr))))
               (pts (cons (list r c) (map (lambda (d) (list (+ r (first d)) (+ c (second d)))) arms))))
         (if (and (= one two) (not (member one '(-1 1))))
          (list r c dr dc one (if (= (at g r c) 1) one (at g r c)) pts) #f)))))))
   (define (frequency v values) (length (filter (lambda (x) (= v x)) values)))
   (define turns
    (apply append
     (for/list ((obj (objects g -1)) #:when (and (= (obj-color obj) 9) (= (length (obj-cells obj)) 5)
              (= (- (obj-r2 obj) (obj-r1 obj)) 2) (= (- (obj-c2 obj) (obj-c1 obj)) 2)))
      (let ((r0 (obj-r1 obj)) (c0 (obj-c1 obj)) (r1 (obj-r2 obj)) (c1 (obj-c2 obj)) (pts (obj-cells obj)))
       (filter (lambda (x) x)
        (for/list ((corner (list c0 c1)) (k '(1 -1)))
         (let ((shape (remove-duplicates
                       (append (for/list ((c (range c0 (+ c1 1)))) (list r0 c))
                               (for/list ((r (range r0 (+ r1 1)))) (list r corner))))))
          (if (not (andmap (lambda (p) (member p pts)) shape)) #f
           (let* ((votes (filter (lambda (v) (not (member v '(-1 1 9))))
                          (apply append (for/list ((p pts))
                           (for/list ((d dirs) #:unless (member (list (+ (first p) (first d)) (+ (second p) (second d))) pts))
                             (value (+ (first p) (first d)) (+ (second p) (second d))))))))
                  (palette (remove-duplicates votes))
                  (source (if (null? palette) (error 'arrows "missing rotation background")
                            (first (sort palette (lambda (a b) (> (frequency a votes) (frequency b votes))))))))
             (list source k pts))))))))))
   (define restored-arrows
    (for/fold ((out g)) ((a arrows))
     (for/fold ((out out)) ((p (list-ref a 6))) (set-cell out (first p) (second p) (list-ref a 4)))))
   (define clean
    (for/fold ((out restored-arrows)) ((t turns))
     (for/fold ((out out)) ((p (third t))) (set-cell out (first p) (second p) (first t)))))
   (define regions (objects clean -1))
   (define actions
    (for/list ((a arrows))
     (let* ((r (first a)) (c (second a)) (dr (third a)) (dc (fourth a)) (source (list-ref a 4))
            (hit (let seek ((y (+ r dr)) (x (+ c dc)))
              (if (not (and (<= 0 y) (< y h) (<= 0 x) (< x w))) (error 'arrows "ray leaves canvas")
               (if (= (at clean y x) source) (seek (+ y dr) (+ x dc)) (list y x)))))
            (target (find-first (lambda (obj) (member hit (obj-cells obj))) regions)))
       (if (not target) (error 'arrows "destination missing")
        (list (if use-payload (list-ref a 5) source) (obj-cells target))))))
   (define painted
    (for/fold ((out clean)) ((action actions))
     (for/fold ((out out)) ((p (second action))) (set-cell out (first p) (second p) (first action)))))
   (define (clockwise p)
    (grid-from-fn (cols p) (rows p) (lambda (r c) (at p (- (rows p) c 1) r))))
   (define steps (modulo (apply + (map second turns)) 4))
   (for/fold ((out painted)) ((k (range steps))) (clockwise out)))))
