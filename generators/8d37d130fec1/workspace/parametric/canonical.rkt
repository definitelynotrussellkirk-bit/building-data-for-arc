(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define bg 8)
             (define objs (objects g bg))
             (define frame (argmax obj-size objs))
             (define fr1 (obj-r1 frame))
             (define fc1 (obj-c1 frame))
             (define fr2 (obj-r2 frame))
             (define fc2 (obj-c2 frame))
             (define frame-color (obj-color frame))
             (define inner-h (- fr2 fr1 1))
             (define inner-w (- fc2 fc1 1))
             (define fill-values
               (for*/list ((r (range (+ fr1 1) fr2)) (c (range (+ fc1 1) fc2))
                   #:when
                   (let ((v (at g r c))) (and (!= v bg) (!= v frame-color))))
                 (at g r c)))
             (define fill-color (mode-list fill-values))
             (define existing-fill
               (for*/list ((r (range (+ fr1 1) fr2)) (c (range (+ fc1 1) fc2))
                   #:when
                   (= (at g r c) fill-color))
                 (list (- r fr1 1) (- c fc1 1))))
             (define top-glyphs
               (filter (lambda (obj)
                         (and
                           (< (obj-r2 obj) fr1)
                           (!= (obj-color obj) bg)
                           (!= (obj-color obj) frame-color)
                           (!= (obj-color obj) fill-color)))
                       (objects-8 g bg)))
             (define (glyph-cell? glyph gr gc)
               (member (list gr gc) (normalize-cells (obj-cells glyph))))
             (define (glyph-allows? glyph rel-r rel-c)
               (let* ((gh (+ 1 (- (obj-r2 glyph) (obj-r1 glyph))))
                      (gw (+ 1 (- (obj-c2 glyph) (obj-c1 glyph)))))
                 (and
                   (zero? (modulo inner-h gh))
                   (zero? (modulo inner-w gw))
                   (let ((bh (quotient inner-h gh))
                         (bw (quotient inner-w gw)))
                     (glyph-cell? glyph (quotient rel-r bh) (quotient rel-c bw))))))
             (define candidates
               (filter (lambda (glyph)
                         (let ((gh (+ 1 (- (obj-r2 glyph) (obj-r1 glyph))))
                               (gw (+ 1 (- (obj-c2 glyph) (obj-c1 glyph)))))
                           (and
                             (> gh 0)
                             (> gw 0)
                             (zero? (modulo inner-h gh))
                             (zero? (modulo inner-w gw))
                             (all? (lambda (p)
                                     (glyph-allows? glyph (first p) (second p)))
                                   existing-fill))))
                       top-glyphs))
             (define glyph
               (first (sort-by candidates
                               (lambda (obj) (+ (* 1000 (obj-r1 obj)) (obj-c1 obj))))))
             (define gh (+ 1 (- (obj-r2 glyph) (obj-r1 glyph))))
             (define gw (+ 1 (- (obj-c2 glyph) (obj-c1 glyph))))
             (define bh (quotient inner-h gh))
             (define bw (quotient inner-w gw))
             (build-grid (+ 1 (- fr2 fr1))
                         (+ 1 (- fc2 fc1))
                         (r c)
                         (cond
                           ((or (zero? r) (zero? c) (= r (- fr2 fr1)) (= c (- fc2 fc1))) frame-color)
                           ((glyph-cell? glyph
                                         (quotient (- r 1) bh)
                                         (quotient (- c 1) bw)) fill-color)
                           (else bg)))))))