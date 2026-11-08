(rule!
 ;; Four equal panels are read row-major inside a uniform separator frame.
 ;; Panel 1 has a long divider plus a singleton side marker. Recover the
 ;; divider by eight-connectivity, then flood its complement by FOUR-neighbor
 ;; moves from the singleton. Panel 2 supplies that marked region; panel 3
 ;; supplies the other. On the divider overlay nonbackground from panel 2
 ;; first, falling back to panel 3. Write panel 4 only, preserving the table.
 ;; Thick exterior borders, horizontal/vertical and 2x2 layouts are supported.
 (lambda (g)
   (let ()
     (define swap-sides #f)
     (define frame (at g 0 0))
     (define (bands xs)
       (if (null? xs) '()
           (let loop ([rest (cdr xs)] [start (car xs)] [end (car xs)] [acc '()])
             (cond [(null? rest) (reverse (cons (list start end) acc))]
                   [(= (car rest) (+ end 1)) (loop (cdr rest) start (car rest) acc)]
                   [else (loop (cdr rest) (car rest) (car rest) (cons (list start end) acc))]))))
     (define row-bands
       (bands (filter (lambda (r) (for/or ([c (range w)]) (not (= (at g r c) frame)))) (range h))))
     (define col-bands
       (bands (filter (lambda (c) (for/or ([r (range h)]) (not (= (at g r c) frame)))) (range w))))
     (define boxes
       (for*/list ([rr row-bands] [cc col-bands])
         (list (first rr) (first cc) (second rr) (second cc))))
     (define panels
       (for/list ([b boxes]) (subgrid g (first b) (second b) (third b) (fourth b))))
     (define instruction (first panels))
     (define first-source (second panels))
     (define second-source (third panels))
     (define destination (fourth boxes))
     (define ph (rows instruction))
     (define pw (cols instruction))
     (define background (at (fourth panels) 0 0))
     (define directions4 '((-1 0) (0 -1) (0 1) (1 0)))
     (define directions8 '((-1 -1) (-1 0) (-1 1) (0 -1) (0 1) (1 -1) (1 0) (1 1)))
     (define domain (for*/list ([r (range ph)] [c (range pw)]) (list r c)))
     (define (flood start allowed directions)
       (define legal (for/fold ([acc (hash)]) ([p allowed]) (hash-set acc p #t)))
       (let loop ([front (list start)] [seen (hash start #t)])
         (define next
           (remove-duplicates
             (for*/list ([p front] [d directions]
                         #:when (let ([q (list (+ (first p) (first d)) (+ (second p) (second d)))])
                                  (and (hash-has-key? legal q) (not (hash-has-key? seen q)))))
               (list (+ (first p) (first d)) (+ (second p) (second d))))))
         (if (null? next) (hash-keys seen)
             (loop next (for/fold ([acc seen]) ([p next]) (hash-set acc p #t))))))
     (define marks (filter (lambda (p) (not (= (at instruction (first p) (second p)) background))) domain))
     (define parts
       (let loop ([todo marks] [acc '()])
         (if (null? todo) (reverse acc)
             (let ([part (flood (first todo) todo directions8)])
               (loop (filter (lambda (p) (not (member p part))) todo) (cons part acc))))))
     (define divider (pick-max parts length))
     (define hint (first (filter (lambda (p) (not (member p divider))) marks)))
     (define selected (flood hint (filter (lambda (p) (not (member p divider))) domain) directions4))
     (for/fold ([out g]) ([p domain])
       (define r (first p))
       (define c (second p))
       (define a (at first-source r c))
       (define b (at second-source r c))
       (define in-selected (if (member p selected) #t #f))
       (define value
         (if (member p divider) (if (= a background) b a)
             (if (if swap-sides (not in-selected) in-selected) a b)))
       (set-cell out (+ (first destination) r) (+ (second destination) c) value)))))
