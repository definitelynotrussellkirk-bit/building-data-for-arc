(rule!
 ;; Singleton colored dots encode a miniature pattern on a spaced lattice.
 ;; Larger solid squares are partial evidence for an enlarged copy. Infer
 ;; their common side length, lattice pitch and translation by matching all
 ;; seed colors and relative coordinates against the miniature. Require a
 ;; unique in-bounds registration disjoint from the miniature, then complete
 ;; every non-background template cell as a square. Keep the miniature intact.
 (lambda (g)
   (let ()
     (define bg (mode g -1))
     (define obs (objects g bg))
     (define dots (filter (lambda (o) (= (obj-size o) 1)) obs))
     (define blocks (filter (lambda (o) (> (obj-size o) 1)) obs))
     (if (or (null? dots) (null? blocks)) g
       (let ()
         (define side (obj-h (first blocks)))
         (define top (min-of obj-r1 dots))
         (define left (min-of obj-c1 dots))
         (define bottom (max-of obj-r1 dots))
         (define right (max-of obj-c1 dots))
         (define differences
           (filter (lambda (n) (> n 0))
             (append (for*/list ((a dots) (b dots)) (abs (- (obj-r1 a) (obj-r1 b))))
                     (for*/list ((a dots) (b dots)) (abs (- (obj-c1 a) (obj-c1 b)))))))
         (if (null? differences) g
           (let ()
             (define spacing (min-list differences))
             (define nr (+ 1 (quotient (- bottom top) spacing)))
             (define nc (+ 1 (quotient (- right left) spacing)))
             (define pattern
               (map (lambda (o) (list (quotient (- (obj-r1 o) top) spacing)
                                     (quotient (- (obj-c1 o) left) spacing) (obj-color o))) dots))
             (define (value r c)
               (let ((p (find-first (lambda (p) (and (= (first p) r) (= (second p) c))) pattern)))
                 (if p (third p) bg)))
             (define first-block (first blocks))
             (define candidates
               (filter
                 (lambda (reg)
                   (let* ((ar (first reg)) (ac (second reg)) (pitch (third reg))
                          (endr (+ ar (* (- nr 1) pitch) side))
                          (endc (+ ac (* (- nc 1) pitch) side)))
                     (and (>= ar 0) (>= ac 0) (<= endr h) (<= endc w)
                          (or (<= endr top) (> ar bottom) (<= endc left) (> ac right))
                          (all? (lambda (b)
                                  (let ((dr (- (obj-r1 b) ar)) (dc (- (obj-c1 b) ac)))
                                    (and (= (obj-h b) side) (= (obj-w b) side)
                                         (= (obj-size b) (* side side))
                                         (>= dr 0) (>= dc 0)
                                         (= (modulo dr pitch) 0) (= (modulo dc pitch) 0)
                                         (= (value (quotient dr pitch) (quotient dc pitch)) (obj-color b))))) blocks))))
                 (for*/list ((pitch (range (+ side 1) (+ (max h w) 1)))
                             (p pattern) #:when (= (third p) (obj-color first-block)))
                   (list (- (obj-r1 first-block) (* (first p) pitch))
                         (- (obj-c1 first-block) (* (second p) pitch)) pitch))))
             (if (not (= (length candidates) 1)) g
               (let* ((reg (first candidates)) (ar (first reg)) (ac (second reg)) (pitch (third reg)))
                 (cellmap g (r c v)
                   (let ((dr (- r ar)) (dc (- c ac)))
                     (if (and (>= dr 0) (>= dc 0)
                              (< (quotient dr pitch) nr) (< (quotient dc pitch) nc)
                              (< (modulo dr pitch) side) (< (modulo dc pitch) side))
                       (let ((color (value (quotient dr pitch) (quotient dc pitch))))
                         (if (= color bg) v color))
                       v))))))))))))
