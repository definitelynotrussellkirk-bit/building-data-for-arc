(rule!
 ;; In a two-color line drawing, erase unsupported diagonal spurs. A spur at
 ;; the end of a cardinal stroke indicates a bent segment: restore the gap
 ;; along that stroke to the next collinear fragment. Preserve breaks without
 ;; an attached bend, isolated straight fragments, and all undamaged strokes.
 ;; Detached diagonal clutter is erased without inventing a repair direction.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define colors (filter (lambda (v) (not (= v bg))) (grid-colors g)))
   (define fg (if (null? colors) bg (first colors)))
   (define dirs '((-1 0) (0 -1) (0 1) (1 0)))
   (define diag '((-1 -1) (-1 1) (1 -1) (1 1)))
   (define (inside r c) (and (<= 0 r) (< r (rows g)) (<= 0 c) (< c (cols g))))
   (define (value grid r c) (if (inside r c) (at grid r c) bg))
   (define initial-spurs
    (for*/list ((r (range (rows g))) (c (range (cols g)))
                #:when (and (not (= (at g r c) bg))
                            (not (for/or ((d dirs)) (= (value g (+ r (first d)) (+ c (second d))) fg)))
                            (for/or ((d diag)) (= (value g (+ r (first d)) (+ c (second d))) fg))))
     (list r c)))
   (define (side-twig r c)
    (define support (filter (lambda (d) (= (value g (+ r (first d)) (+ c (second d))) fg)) dirs))
    (and (= (at g r c) fg) (= (length support) 1)
         (for/or ((d diag)) (member (list (+ r (first d)) (+ c (second d))) initial-spurs))
         (let* ((dr (first (first support))) (dc (second (first support)))
                (rr (+ r dr)) (cc (+ c dc)))
          (and (= (value g (+ rr dc) (+ cc dr)) fg) (= (value g (- rr dc) (- cc dr)) fg)
               (not (for/or ((k (range 1 (max (rows g) (cols g)))))
                       (= (value g (- r (* k dr)) (- c (* k dc))) fg)))))))
   (define spurs (remove-duplicates
                  (append initial-spurs
                   (for*/list ((r (range (rows g))) (c (range (cols g))) #:when (and (not (= (at g r c) bg)) (side-twig r c))) (list r c)))))
   (define cleaned (for/fold ((out g)) ((p spurs)) (set-cell out (first p) (second p) bg)))
   (define repair-mode 'cued)
   (define (repair r c d)
    (define dr (first d)) (define dc (second d))
    (define cue (or (member (list (+ r dr dc) (+ c dc dr)) spurs)
                   (member (list (- (+ r dr) dc) (- (+ c dc) dr)) spurs)))
    (if (and (not (equal? repair-mode 'none))
             (or (not (equal? repair-mode 'horizontal)) (= dr 0))
             (or (not (equal? repair-mode 'vertical)) (= dc 0))
             (= (value cleaned r c) fg)
             (= (value cleaned (- r dr) (- c dc)) fg)
             (= (value cleaned (+ r dr) (+ c dc)) bg)
             (or cue (equal? repair-mode 'all_gaps)))
        (let ray ((rr (+ r dr)) (cc (+ c dc)) (gap '()))
         (cond ((not (inside rr cc)) '())
               ((= (at cleaned rr cc) fg) gap)
               (else (ray (+ rr dr) (+ cc dc) (cons (list rr cc) gap)))))
        '()))
   (define repaired
    (remove-duplicates
     (apply append (for*/list ((p (find-color cleaned fg)) (d dirs)) (repair (first p) (second p) d)))))
   (define completed (for/fold ((out cleaned)) ((p repaired)) (set-cell out (first p) (second p) fg)))
   (define finish 'straighten)
   (define junction-grid completed)
   (define candidates repaired)
   (if (equal? finish 'straighten) completed
    (for/fold ((out completed)) ((p candidates))
     (define degree (for/sum ((d dirs))
                     (if (= (value junction-grid (+ (first p) (first d)) (+ (second p) (second d))) fg) 1 0)))
     (if (>= degree 3) (set-cell out (first p) (second p) 7) out))))))
