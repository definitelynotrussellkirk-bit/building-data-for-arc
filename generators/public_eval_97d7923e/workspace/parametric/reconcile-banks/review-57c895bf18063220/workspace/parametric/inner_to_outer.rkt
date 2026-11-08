(rule!
 ;; Each cue is a vertical stack of an endpoint color outside all bars. Its
 ;; height k selects the kth matching bar in outer-to-inner (top-row) order;
 ;; replace that bar's uniform filler with the endpoint color.
 (lambda (g)
  (let ()
   (define reverse-order? #t)
   (define fixed-rank 0)
   (define recolor-all? #f)
   (define h (rows g))
   (define w (cols g))
   (define bg (mode g -1))
   (define (segments c)
    (let loop ([r 0] [out '()])
     (cond
      [(>= r h) (reverse out)]
      [(= (at g r c) bg) (loop (+ r 1) out)]
      [else
       (define end
        (let scan ([e r])
         (if (and (< (+ e 1) h) (not (= (at g (+ e 1) c) bg)))
             (scan (+ e 1)) e)))
       (loop (+ end 1) (cons (list r end) out))])))
   ;; Bar record: column, top, bottom, endpoint color, filler color.
   (define bars
    (apply append
     (for/list ([c (in-range w)])
      (filter-map
       (lambda (seg)
        (define top (first seg))
        (define bottom (second seg))
        (if (< (- bottom top) 2) #f
         (let ([endpoint (at g top c)] [filler (at g (+ top 1) c)])
          (if (and (= (at g bottom c) endpoint)
                   (not (= filler bg)) (not (= filler endpoint))
                   (for/and ([r (in-range (+ top 1) bottom)])
                    (= (at g r c) filler)))
              (list c top bottom endpoint filler) #f))))
       (segments c)))))
   (define colors (sort (remove-duplicates (map fourth bars)) <))
   (define (bar-cell? r c)
    (for/or ([bar (in-list bars)])
     (and (= c (first bar)) (<= (second bar) r) (<= r (third bar)))))
   (define (cue-run c color)
    (let loop ([r 0] [current 0] [best 0])
     (if (= r h) (max current best)
      (if (and (= (at g r c) color) (not (bar-cell? r c)))
          (loop (+ r 1) (+ current 1) best)
          (loop (+ r 1) 0 (max current best))))))
   (define (cue-height color)
    (apply max (for/list ([c (in-range w)]) (cue-run c color))))
   (define (bar<? a b)
    (if (= (second a) (second b))
        (< (first a) (first b))
        (< (second a) (second b))))
   (define (interior bar)
    (for/list ([r (in-range (+ (second bar) 1) (third bar))])
     (list r (first bar))))
   (for/fold ([out g]) ([color (in-list colors)])
    (define group (sort (filter (lambda (bar) (= (fourth bar) color)) bars) bar<?))
    (define ordered (if reverse-order? (reverse group) group))
    (define rank (if (> fixed-rank 0) fixed-rank (cue-height color)))
    (define chosen
     (if recolor-all? ordered
      (if (and (>= rank 1) (<= rank (length ordered)))
          (list (list-ref ordered (- rank 1))) '())))
    (for/fold ([painted out]) ([bar (in-list chosen)])
     (recolor-cells painted (interior bar) color))))))
