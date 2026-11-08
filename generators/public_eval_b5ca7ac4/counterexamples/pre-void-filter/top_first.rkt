(rule!
 ;; Recover each complete 2- or 8-framed rectangle with a uniform different interior.
 ;; Keep its row, size, frame and fill. Border-8 frames pack left; border-2 pack right.
 ;; Within each direction, process topmost original rows first.
 ;; Every later placement consumes the UPDATED positions of overlapping prior boxes.
 ;; The majority cell value, including zero, is the background. No original-grid lookup.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define boxes
    (for*/list ((r (range (- (rows g) 2))) (c (range (- (cols g) 2)))
                #:when (and (member (at g r c) '(2 8))
                            (= (at g r c) (at g (+ r 1) c))
                            (= (at g r c) (at g r (+ c 1)))
                            (not (= (at g r c) (at g (+ r 1) (+ c 1)))))
                (rr (range (+ r 2) (rows g))) (cc (range (+ c 2) (cols g)))
                #:when (and (= (at g r c) (at g rr c))
                            (= (at g r c) (at g r cc))
                            (= (at g r c) (at g rr cc))
                   (for*/and ((i (range r (+ rr 1))) (j (range c (+ cc 1))))
                    (= (at g i j) (if (or (= i r) (= i rr) (= j c) (= j cc))
                                      (at g r c) (at g (+ r 1) (+ c 1)))))))
      (list r c (+ 1 (- rr r)) (+ 1 (- cc c)) (at g r c) (at g (+ r 1) (+ c 1)) c)))
   (define (priority left? a b)
    (if (= (first a) (first b))
      (if left? (< (second a) (second b)) (> (second a) (second b)))
      (< (first a) (first b))))
   (define (settled-col o) (second o))
   (define (pack border left?)
    (define ordered
      (sort (filter (lambda (b) (= (list-ref b 4) border)) boxes)
            (lambda (a b) (priority left? a b))))
    (for/fold ((done '())) ((b ordered))
     (let* ((hits (filter (lambda (p)
                    (and (< (first b) (+ (first p) (third p)))
                         (< (first p) (+ (first b) (third b))))) done))
            (dest (if left?
                    (if (null? hits) 0
                        (apply max (map (lambda (o) (+ (settled-col o) (fourth o))) hits)))
                    (if (null? hits) (- (cols g) (fourth b))
                        (- (apply min (map settled-col hits)) (fourth b))))))
       (append done (list (list (first b) dest (third b) (fourth b)
                               (list-ref b 4) (list-ref b 5) (second b)))))))
   (define placed (append (pack 8 #t) (pack 2 #f)))
   (for*/fold ((out (empty-grid (rows g) (cols g) bg)))
               ((b placed) (i (range (third b))) (j (range (fourth b))))
    (let ((r (+ (first b) i)) (c (+ (second b) j)))
     (if (in-bounds? r c (rows g) (cols g))
       (set-cell out r c
         (if (or (= i 0) (= j 0) (= i (- (third b) 1)) (= j (- (fourth b) 1)))
             (list-ref b 4) (list-ref b 5))) out))))))
