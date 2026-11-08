(rule!
 ;; Hollow 4x4 blocks on a coarse lattice form one big cyan(8) group
 ;; and small colored groups; a blue(1) bar marks the gravity edge.
 ;; Per lattice slice (column of the cyan group when it is wide, row
 ;; when tall), count the cyan blocks and the overlapping small-group
 ;; blocks, and emit stacked bars: cyan pressed toward the blue bar,
 ;; the small color on top, empty above.
 (lambda (g)
   (let ()
     (define (analyze col)  ;; (color bh bw blocks r1 c1) on the lattice
       (let* ((cells (find-color g col))
              (r1 (min-list (map first cells)))
              (c1 (min-list (map second cells)))
              (bh (quotient (+ (- (max-list (map first cells)) r1) 2) 4))
              (bw (quotient (+ (- (max-list (map second cells)) c1) 2) 4)))
         (list col bh bw
               (map (lambda (br)
                      (map (lambda (bc)
                             (if (= (at g (+ r1 (* br 4)) (+ c1 (* bc 4)))
                                    col)
                                 1 0))
                           (range 0 bw)))
                    (range 0 bh))
               r1 c1)))
     (define (i-color i) (nth i 0))
     (define (i-bh i) (nth i 1))
     (define (i-bw i) (nth i 2))
     (define (i-blocks i) (nth i 3))
     (define (i-r1 i) (nth i 4))
     (define (i-c1 i) (nth i 5))
     (define infos
       (map analyze (filter (lambda (c) (and (not (= c 0)) (not (= c 1))))
                            (grid-colors g))))
     (define main (find (lambda (i) (= (i-color i) 8)) infos))
     (define smalls (filter (lambda (i) (not (= (i-color i) 8))) infos))
     (define horizontal? (> (i-bw main) (i-bh main)))
     (define main-at-end  ;; cyan sits past the smalls, away from the bar
       (if horizontal?
           (> (- (i-r1 main)
                 (quotient (apply + (map i-r1 smalls)) (length smalls)))
              0)
           (> (- (i-c1 main)
                 (quotient (apply + (map i-c1 smalls)) (length smalls)))
              0)))
     (define (col-sum blocks i n)
       (sum-list (map (lambda (br) (nth (nth blocks br) i)) (range 0 n))))
     (define (slice-counts i)  ;; (cyan-count small-count small-color)
       (let* ((m-count (if horizontal?
                           (col-sum (i-blocks main) i (i-bh main))
                           (sum-list (nth (i-blocks main) i))))
              (s-info (find (lambda (si)
                              (let ((off (if horizontal?
                                             (quotient (- (i-c1 si)
                                                          (i-c1 main))
                                                       4)
                                             (quotient (- (i-r1 si)
                                                          (i-r1 main))
                                                       4))))
                                (and (>= i off)
                                     (< i (+ off (if horizontal?
                                                     (i-bw si)
                                                     (i-bh si)))))))
                            smalls)))
         (list m-count
               (if s-info
                   (if horizontal?
                       (col-sum (i-blocks s-info)
                                (- i (quotient (- (i-c1 s-info)
                                                  (i-c1 main))
                                               4))
                                (i-bh s-info))
                       (sum-list (nth (i-blocks s-info)
                                      (- i (quotient (- (i-r1 s-info)
                                                        (i-r1 main))
                                                     4)))))
                   0)
               (if s-info (i-color s-info) 0))))
     (define n-slices (if horizontal? (i-bw main) (i-bh main)))
     (define slices (map slice-counts (range 0 n-slices)))
     (define max-h (max-of (lambda (s) (+ (first s) (second s))) slices))
     (define (bar triple)  ;; one stacked slice, padded to max-h
       (let ((m (make-list (first triple) 8))
             (s (make-list (second triple) (third triple)))
             (p (make-list (- max-h (+ (first triple) (second triple)))
                           0)))
         (if main-at-end (append p s m) (append m s p))))
     (define stacks (map bar slices))
     (if horizontal?
         (map (lambda (r) (map (lambda (c) (nth (nth stacks c) r))
                               (range 0 n-slices)))
              (range 0 max-h))
         stacks))))