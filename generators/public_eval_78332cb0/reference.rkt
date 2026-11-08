(rule!
 ;; Split at complete magenta (6) divider bands into equal-sized panels.
 ;; Orange (7) is background. Match WHOLE foreground contact sets, ignoring
 ;; color, across opposite borders. The unique open head-to-tail chain fixes
 ;; its order and whether the panels must be laid out vertically or horizontally.
 ;; Preserve panel pixels and divider thickness; do not rotate the panels.
 ;; Optional prefix_parity highlights panels with an odd cumulative foreground
 ;; cell count in the reconstructed chain, not in their input presentation order.
 (lambda (g)
  (let ()
   (define count-policy "canonical")
   (define prefix-scope "assembled")
   (define height (length g))
   (define width (length (first g)))
   (define (spans flags)
    (let loop ([i 0] [start #f] [out '()])
     (cond [(= i (length flags)) (if start (append out (list (list start i))) out)]
           [(list-ref flags i) (loop (+ i 1) #f (if start (append out (list (list start i))) out))]
           [else (loop (+ i 1) (if start start i) out)])))
   (define rr (spans (for/list ([row g]) (andmap (lambda (v) (= v 6)) row))))
   (define cc (spans (for/list ([c (range width)]) (andmap (lambda (row) (= (list-ref row c) 6)) g))))
   (define thick (if (> (length rr) 1) (- (first (second rr)) (second (first rr)))
                     (- (first (second cc)) (second (first cc)))))
   (define tiles
    (for*/list ([rb rr] [cb cc])
     (for/list ([r (range (first rb) (second rb))])
      (for/list ([c (range (first cb) (second cb))]) (list-ref (list-ref g r) c)))))
   (define n (length tiles))
   (define th (length (first tiles)))
   (define tw (length (first (first tiles))))
   (define (edge t axis end?)
    (define vals (if (equal? axis "vertical") (if end? (last t) (first t))
                       (map (lambda (row) (if end? (last row) (first row))) t)))
    (for/list ([i (range (length vals))] #:when (not (= (list-ref vals i) 7))) i))
   (define (search axis path)
    (define port (edge (list-ref tiles (last path)) axis #t))
    (cond [(= (length path) n) (if (null? port) (list path) '())]
          [(null? port) '()]
          [else (apply append
           (for/list ([i (range n)] #:when (and (not (member i path))
                     (equal? port (edge (list-ref tiles i) axis #f))))
            (search axis (append path (list i)))))]))
   (define candidates
    (apply append
     (for/list ([axis (list "vertical" "horizontal")])
      (apply append
       (for/list ([i (range n)] #:when (null? (edge (list-ref tiles i) axis #f)))
        (map (lambda (path) (list axis path)) (search axis (list i))))))))
   (define axis (first (first candidates)))
   (define order (second (first candidates)))
   (define (area t) (for*/sum ([row t] [v row]) (if (= v 7) 0 1)))
   (define score-order (if (equal? prefix-scope "input") (range n) order))
   (define (prefix-count target)
    (let loop ([rest score-order] [total 0])
     (define i (first rest))
     (define next (+ total (area (list-ref tiles i))))
     (if (= i target) next (loop (rest-list rest) next))))
   (define (rest-list xs) (cdr xs))
   (define ordered
    (for/list ([i order])
     (define change? (and (equal? count-policy "prefix_parity") (odd? (prefix-count i))))
     (for/list ([row (list-ref tiles i)])
      (map (lambda (v) (if (and change? (not (= v 7))) 8 v)) row))))
   (if (equal? axis "vertical")
    (apply append (for/list ([i (range n)])
      (append (list-ref ordered i) (if (= i (- n 1)) '() (make-list thick (make-list tw 6))))))
    (for/list ([r (range th)])
     (apply append (for/list ([i (range n)])
      (append (list-ref (list-ref ordered i) r) (if (= i (- n 1)) '() (make-list thick 6))))))))))
