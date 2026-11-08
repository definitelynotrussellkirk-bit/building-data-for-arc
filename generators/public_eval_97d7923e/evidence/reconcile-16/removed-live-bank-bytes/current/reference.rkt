(rule!
 ;; Each top-row color run encodes a 1-based rank.  For that color, find
 ;; vertical wires whose same-color endpoints enclose a uniform nonzero
 ;; interior of another color.  Sort by interior length descending and recolor
 ;; the ranked wire.  The alternate setting then uses the stage-A result to
 ;; choose the longest selected wire and activate its horizontal 9-filled relay.
 (lambda (g)
  (let ()
   (define relay-mode "rank_only")
   (define rival "")
   (define h (rows g))
   (define w (cols g))
   (define (run-length c color)
    (let loop ([r 0])
     (if (and (< r h) (= (at g r c) color)) (loop (+ r 1)) r)))
   (define legends
    (for/list ([c (in-range w)] #:when (!= (at g 0 c) 0))
     (list (at g 0 c) (run-length c (at g 0 c)) c)))
   (define (middle-fill color c top bottom)
    (if (< (- bottom top) 2) #f
     (let ([v (at g (+ top 1) c)])
      (and (!= v 0) (!= v color)
       (for/and ([r (in-range (+ top 1) bottom)]) (= (at g r c) v))
       v))))
   (define (record<? a b)
    (or (> (first a) (first b))
        (and (= (first a) (first b))
             (or (< (second a) (second b))
                 (and (= (second a) (second b)) (< (third a) (third b)))))))
   (define (candidates color)
    (sort
     (for*/list ([c (in-range w)] [top (in-range (- h 2))]
                 [bottom (in-range (+ top 2) h)]
                 #:when (= (at g top c) color)
                 #:when (= (at g bottom c) color)
                 #:when (middle-fill color c top bottom))
      (list (- bottom top 1) top c bottom (at g (+ top 1) c)))
     record<?))
   (define (select-record entry)
    (let* ([color (first entry)] [rank (second entry)] [records (candidates color)])
     (and (<= rank (length records)) (list-ref records (- rank 1)))))
   (define selected
    (filter (lambda (p) (second p))
     (for/list ([entry legends]) (list entry (select-record entry)))))
   (define (fill-vertical out pair)
    (let* ([entry (first pair)] [record (second pair)] [color (first entry)]
           [top (second record)] [c (third record)] [bottom (fourth record)])
     (for/fold ([canvas out]) ([r (in-range (+ top 1) bottom)])
      (set-cell canvas r c color))))
   (define stage-a (for/fold ([out g]) ([pair selected]) (fill-vertical out pair)))
   (define (solid-in-stage? color record)
    (let ([top (second record)] [c (third record)] [bottom (fourth record)])
     (for/and ([r (in-range top (+ bottom 1))]) (= (at stage-a r c) color))))
   (define stage-selected
    (filter (lambda (p) (second p))
     (for/list ([entry legends])
      (let ([color (first entry)])
       (list entry (for/first ([record (in-list (candidates color))]
                              #:when (solid-in-stage? color record)) record))))))
   (define raw-longest
    (for/list ([entry legends]) (list entry (first (candidates (first entry))))))
   (define (pick-longest pairs)
    (for/fold ([best #f]) ([pair pairs])
     (if (or (not best) (> (first (second pair)) (first (second best)))) pair best)))
   (define winner
    (if (equal? rival "relay_longest_candidate")
        (pick-longest raw-longest)
        (pick-longest stage-selected)))
   (define (relay-records color)
    (for*/list ([r (in-range h)] [left (in-range (- w 2))]
                [right (in-range (+ left 2) w)]
                #:when (= (at g r left) color)
                #:when (= (at g r right) color)
                #:when (for/and ([c (in-range (+ left 1) right)]) (= (at g r c) 9)))
     (list r left right)))
   (define (fill-relay out record color)
    (for/fold ([canvas out]) ([c (in-range (+ (second record) 1) (third record))])
     (set-cell canvas (first record) c color)))
   (if (and (equal? relay-mode "selected_longest") winner)
       (for/fold ([out stage-a]) ([record (relay-records (first (first winner)))])
        (fill-relay out record (first (first winner))))
       stage-a))))
