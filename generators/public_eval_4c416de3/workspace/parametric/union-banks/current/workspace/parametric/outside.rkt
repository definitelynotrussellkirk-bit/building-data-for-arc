(rule!
 ;; Black rectangular outlines carry colored marks beside their corners.
 ;; Infer each corner's inward axes from its two black arms. Assign marks
 ;; to their nearest corner and normalize those positions to inward axes.
 ;; The largest complete colored motif teaches the common shape. Copy that
 ;; shape, recolored and reflected into each marked corner's local axes.
 ;; Partial frames and clipped stamps are legal. Preserve unrelated cells.
 ;; Equal nearest distances and equal exemplar sizes use row-major order;
 ;; admitted generated scenes avoid conflicting exemplar interpretations.
 (lambda (g)
   (let ()
     (define outside-only #t)
     (define colors (filter (lambda (v) (> (count-color g v) 0)) (range 1 10)))
     (define background (pick-max colors (lambda (v) (count-color g v))))
     (define (black? r c) (= (safe-at g r c -1) 0))
     (define corners
       (for*/list ([r (range h)] [c (range w)] [sr '(-1 1)] [sc '(-1 1)]
                   #:when
                   (and (not (black? (- r sr) c)) (not (black? r (- c sc)))
                        (>= (for/sum ([k '(1 2 3)]) (if (black? (+ r (* k sr)) c) 1 0)) 2)
                        (>= (for/sum ([k '(1 2 3)]) (if (black? r (+ c (* k sc))) 1 0)) 2)))
         (list r c sr sc)))
     (define marks
       (for*/list ([r (range h)] [c (range w)]
                   #:when (and (not (= (at g r c) 0)) (not (= (at g r c) background))))
         (define corner
           (pick-min corners
             (lambda (q) (+ (* (- r (first q)) (- r (first q)))
                            (* (- c (second q)) (- c (second q)))))))
         (list corner r c (at g r c))))
     (define groups
       (for/list ([q corners] #:when (ormap (lambda (p) (equal? (first p) q)) marks))
         (define selected (filter (lambda (p) (equal? (first p) q)) marks))
         (list q (fourth (first selected))
               (for/list ([p selected])
                 (list (* (- (second p) (first q)) (third q))
                       (* (- (third p) (second q)) (fourth q)))))))
     (define exemplar (pick-max groups (lambda (x) (length (third x)))))
     (define motif (third exemplar))
     (for/fold ([out g]) ([group groups])
       (define q (first group))
       (for/fold ([result out]) ([p motif])
         (define r (+ (first q) (* (third q) (first p))))
         (define c (+ (second q) (* (fourth q) (second p))))
         (if (and (<= 0 r) (< r h) (<= 0 c) (< c w)
                  (or (not outside-only) (<= (first p) 0) (<= (second p) 0)))
             (set-cell result r c (second group)) result))))))
