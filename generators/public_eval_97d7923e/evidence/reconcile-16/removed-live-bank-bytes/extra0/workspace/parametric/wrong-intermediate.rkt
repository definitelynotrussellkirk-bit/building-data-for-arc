(rule!
 ;; Count each color in the detached legend.  For that color, rank vertical
 ;; endpoint-matched rods by payload length (longest first) and recolor the
 ;; legend-count-ranked rod's payload to its endpoint color.
 (lambda (g)
  (let ()
   (define H (rows g))
   (define W (cols g))
   (define (run-bottom c top)
    (let loop ([r top])
     (if (and (< (+ r 1) H) (not (= (at g (+ r 1) c) 0)))
         (loop (+ r 1)) r)))
   (define (column-rods c)
    (let loop ([r 0] [acc '()])
     (cond
      [(>= r H) (reverse acc)]
      [(= (at g r c) 0) (loop (+ r 1) acc)]
      [else
       (define top r)
       (define bottom (run-bottom c top))
       (define interior
        (for/list ([rr (range (+ top 1) bottom)]) (at g rr c)))
       (define endpoint (at g top c))
       (define valid
        (and (>= (- bottom top) 2)
             (= endpoint (at g bottom c))
             (not (= endpoint 0))
             (pair? interior)
             (not (= (first interior) 0))
             (not (= (first interior) endpoint))
             (andmap (lambda (v) (= v (first interior))) interior)))
       (loop (+ bottom 1)
             (if valid
                 (cons (list endpoint (first interior) top bottom c (length interior)) acc)
                 acc))])))
   (define rods (apply append (for/list ([c (range W)]) (column-rods c))))
   (define (covered? r c)
    (ormap (lambda (rod)
             (and (= c (list-ref rod 4))
                  (<= (list-ref rod 2) r)
                  (<= r (list-ref rod 3))))
           rods))
   (define key-cells
    (for*/list ([r (range H)] [c (range W)]
                #:when (and (not (= (at g r c) 0)) (not (covered? r c))))
     (list r c (at g r c))))
   (define colors (remove-duplicates (map third key-cells)))
   (define (rod<? a b)
    (cond
     [(not (= (list-ref a 5) (list-ref b 5))) (> (list-ref a 5) (list-ref b 5))]
     [(not (= (list-ref a 2) (list-ref b 2))) (< (list-ref a 2) (list-ref b 2))]
     [else (< (list-ref a 4) (list-ref b 4))]))
   ;; A: derive the color-specific ranked rods selected by the input legend.
   (define selected
    (for/list ([color colors])
     (define rank (count (lambda (p) (= (third p) color)) key-cells))
     (define candidates
      (sort (filter (lambda (rod) (= (first rod) color)) rods) rod<?))
     (list-ref candidates (- rank 1))))
   ;; B: consume those selected records to recolor exactly their payloads.
   (define ranked
    (for/fold ([out g]) ([rod selected])
     (for/fold ([canvas out]) ([r (range (+ (list-ref rod 2) 1) (list-ref rod 3))])
      (set-cell canvas r (list-ref rod 4) (first rod)))))
   ;; Counterfactual: skip the legend-ranked intermediate and highlight the
   ;; globally longest raw rod instead.
   (define winner (pick-max rods (lambda (rod) (list-ref rod 5))))
   (for/fold ([out ranked]) ([r (range (list-ref winner 2) (+ (list-ref winner 3) 1))])
    (set-cell out r (list-ref winner 4) 9)))))
