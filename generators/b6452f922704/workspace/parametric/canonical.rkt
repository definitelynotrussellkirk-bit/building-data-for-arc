(rule!
 ;; Maroon(9) frames each hold a red(2) and a blue(1) shape whose
 ;; bounding boxes overlap, plus a KEY color dot just above the frame.
 ;; Emit one solid key-colored block per frame, sized like that
 ;; red/blue overlap — laid out in a row, vertically centered, with
 ;; 1-column gaps.
 (lambda (g)
   (let ()
     (define (frame? o)  ;; hollow maroon rectangle outline, 3x3+
       (and (= (obj-color o) 9)
            (>= (obj-h o) 3) (>= (obj-w o) 3)
            (= (obj-size o) (- (* 2 (+ (obj-h o) (obj-w o))) 4))
            (all? (lambda (p) (or (= (first p) (obj-r1 o))
                                  (= (first p) (obj-r2 o))
                                  (= (second p) (obj-c1 o))
                                  (= (second p) (obj-c2 o))))
                  (obj-cells o))))
     (define frames
       (sort (filter frame? (objects g 0))
             (lambda (a b) (or (< (obj-r1 a) (obj-r1 b))
                               (and (= (obj-r1 a) (obj-r1 b))
                                    (< (obj-c1 a) (obj-c1 b)))))))
     (define (key-of fr)
       (let ((r (- (obj-r1 fr) 1)))
         (first (if (>= r 0)
                    (filter (lambda (v) (not (member? v (list 0 9))))
                            (map (lambda (c) (at g r c))
                                 (range (obj-c1 fr)
                                        (+ (obj-c2 fr) 1))))
                    (list)))))
     (define (part-of fr)  ;; the red/blue bbox overlap as a key block
       (let* ((interior (subgrid g (+ (obj-r1 fr) 1) (+ (obj-c1 fr) 1)
                                 (- (obj-r2 fr) 1) (- (obj-c2 fr) 1)))
              (rb (bbox-of-cells (find-color interior 2)))
              (bb (bbox-of-cells (find-color interior 1))))
         (empty-grid (+ 1 (- (min (third rb) (third bb))
                             (max (first rb) (first bb))))
                     (+ 1 (- (min (fourth rb) (fourth bb))
                             (max (second rb) (second bb))))
                     (key-of fr))))
     (define parts (map part-of frames))
     (let ((gh (apply max (map rows parts)))
           (gw (+ (apply + (map cols parts)) (- (length parts) 1))))
       (let loop ((xs parts) (left 0) (out (empty-grid gh gw 0)))
         (if (empty? xs)
             out
             (let ((piece (first xs)))
               (loop (rest xs) (+ left (cols piece) 1)
                     (for*/fold ((acc out))
                                ((r (range 0 (rows piece)))
                                 (c (range 0 (cols piece))))
                       (let ((v (at piece r c)))
                         (if (> v 0)
                             (set-cell acc
                                       (+ (quotient (- gh (rows piece))
                                                    2)
                                          r)
                                       (+ left c) v)
                             acc)))))))))))