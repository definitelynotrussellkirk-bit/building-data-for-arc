(rule!
 ;; Assemble disconnected connector-bearing pieces by translation only. The
 ;; yellow piece stays fixed. Bodies never overlap; red connectors overlap in
 ;; pairs, and every connector must be consumed. Connector normals need not be
 ;; opposite: corner contacts are legal. The admitted grammar has one assembly.
 ;; In the alternative policy, recover the red-contact graph of that assembly
 ;; and recolor the unique deepest piece from the yellow anchor to cyan.
 (lambda (g)
   (let ()
     (define output-policy "assemble")
     (define raw-pieces (objects-multicolor g 0))
     (define pieces
       (for/list ((o raw-pieces) (id (range (length raw-pieces))))
         (list id (for/list ((p (obj-cells o)))
                    (list (first p) (second p) (at g (first p) (second p)))))))
     (define (cells piece) (second piece))
     (define (reds triples)
       (for/list ((p triples) #:when (= (third p) 2)) (take p 2)))
     (define (yellow? piece) (for/or ((p (cells piece))) (= (third p) 4)))
     (define anchor (first (filter yellow? pieces)))
     (define anchor-id (first anchor))
     (define (shift piece dr dc)
       (list (first piece)
             (for/list ((p (cells piece)))
               (list (+ dr (first p)) (+ dc (second p)) (third p)))))
     (define (valid? piece board open)
       (for/and ((p (cells piece)))
         (and (in-bounds? (first p) (second p) h w)
              (or (= (at board (first p) (second p)) 0)
                  (and (= (third p) 2)
                       (= (at board (first p) (second p)) 2)
                       (member (take p 2) open))))))
     (define (options target pending board open)
       (for*/list ((piece pending) (port (reds (cells piece)))
                   #:do ((define moved (shift piece (- (first target) (first port))
                                                  (- (second target) (second port)))))
                   #:when (valid? moved board open))
         moved))
     (define (search placed pending board open)
       (cond
         ((null? pending) (and (null? open) placed))
         ((null? open) #f)
         (else
          (define choices
            (for/list ((target open)) (options target pending board open)))
          (define best (pick-min choices length))
          (for/or ((piece best))
            (define ports (reds (cells piece)))
            (define next-open
              (append (filter (lambda (p) (not (member p ports))) open)
                      (filter (lambda (p) (not (member p open))) ports)))
            (search (cons piece placed)
                    (filter (lambda (p) (not (= (first p) (first piece)))) pending)
                    (paint-cells board (cells piece)) next-open)))))
     (define solution
       (search (list anchor)
               (filter (lambda (p) (not (= (first p) anchor-id))) pieces)
               (paint-cells (empty-grid h w 0) (cells anchor)) (reds (cells anchor))))
     (define (joined? a b)
       (for/or ((p (reds (cells a)))) (member p (reds (cells b)))))
     (define (graph-depths entries)
       (let visit ((frontier (list anchor)) (seen (list anchor-id))
                   (depth 0) (distances (list (list anchor-id 0))))
         (define next
           (filter (lambda (p)
                     (and (not (member (first p) seen))
                          (for/or ((q frontier)) (joined? p q)))) entries))
         (if (null? next) distances
             (visit next (append seen (map first next)) (+ depth 1)
                    (append distances (map (lambda (p) (list (first p) (+ depth 1))) next))))))
     (define (top-left piece)
       (list (apply min (map first (cells piece)))
             (apply min (map second (cells piece)))))
     (define (render entries)
       (for/fold ((board (empty-grid h w 0))) ((p entries)) (paint-cells board (cells p))))
     (if (not solution) g
         (let* ((assembled (render solution))
                (ordered (sort solution < #:key first))
                (distances (graph-depths ordered))
                (moving (filter (lambda (p) (not (= (first p) anchor-id))) ordered))
                (origin (top-left anchor))
                (target
                  (cond
                    ((equal? output-policy "largest_original") (pick-max moving (lambda (p) (length (cells p)))))
                    ((equal? output-policy "smallest_original") (pick-min moving (lambda (p) (length (cells p)))))
                    ((equal? output-policy "most_ports") (pick-max moving (lambda (p) (length (reds (cells p))))))
                    ((equal? output-policy "last_input") (last moving))
                    ((equal? output-policy "shallowest") (pick-min moving (lambda (p) (second (assoc (first p) distances)))))
                    ((equal? output-policy "euclidean")
                     (pick-max moving (lambda (p)
                       (define pt (top-left p))
                       (+ (sqr (- (first pt) (first origin)))
                          (sqr (- (second pt) (second origin)))))))
                    (else (pick-max moving (lambda (p) (second (assoc (first p) distances))))))))
           (if (equal? output-policy "assemble") assembled
               (for/fold ((board assembled))
                         ((p (if (equal? output-policy "all_movers") moving (list target))))
                 (recolor-cells board
                   (map (lambda (c) (take c 2)) (filter (lambda (c) (not (= (third c) 2))) (cells p))) 8))))))))
