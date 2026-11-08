(rule!
 ;; Squares are nodes; same-color eight-connected pipe components are edges.
 ;; Infer background and pipe color structurally. The node color appearing
 ;; exactly twice identifies the endpoints. Find a minimum-hop route (or,
 ;; alternatively, minimum pipe-ink route). Break ties by node reading order.
 ;; Paint route pipes 5 and intermediate squares 3, preserving endpoints.
 (lambda (g)
  (let ()
   (define metric 'fewest_edges)
   (define bg (mode g -1))
   (define objs (objects-8 g bg))
   (define colors (filter (lambda (k) (not (= k bg))) (grid-colors g)))
   (define (square? o)
    (and (>= (obj-h o) 2) (= (obj-h o) (obj-w o))
         (= (obj-size o) (* (obj-h o) (obj-w o)))))
   (define pipe-color
    (first (filter (lambda (k)
      (for/or ([o objs]) (and (= (obj-color o) k) (not (square? o))))) colors)))
   (define nodes (filter (lambda (o) (not (= (obj-color o) pipe-color))) objs))
   (define pipes (filter (lambda (o) (= (obj-color o) pipe-color)) objs))
   (define endpoint-color
    (first (filter (lambda (k) (= (length (filter (lambda (o) (= (obj-color o) k)) nodes)) 2)) colors)))
   (define endpoints
    (filter (lambda (i) (= (obj-color (list-ref nodes i)) endpoint-color)) (range (length nodes))))
   (define (touches? a b)
    (for/or ([p (obj-cells a)])
     (for/or ([q (obj-cells b)])
      (and (<= (abs (- (first p) (first q))) 1)
           (<= (abs (- (second p) (second q))) 1)))))
   (define edges
    (for/list ([pipe pipes])
     (let ([ends (filter (lambda (i) (touches? pipe (list-ref nodes i))) (range (length nodes)))])
      (list (first ends) (second ends) (obj-cells pipe)))))
   (define (lex<? a b)
    (cond [(null? a) (not (null? b))] [(null? b) #f]
          [(< (first a) (first b)) #t] [(> (first a) (first b)) #f]
          [else (lex<? (rest a) (rest b))]))
   (define (state<? a b)
    (or (< (first a) (first b))
        (and (= (first a) (first b)) (lex<? (second a) (second b)))))
   (define route
    (let loop ([queue (list (list 0 (list (first endpoints)) '()))] [visited '()])
     (if (null? queue) (list 0 '() '())
      (let* ([ordered (sort queue state<?)] [state (first ordered)]
             [node (last (second state))])
       (cond [(member node visited) (loop (rest ordered) visited)]
             [(= node (second endpoints)) state]
             [else
              (let ([more
               (filter (lambda (v) v)
                (for/list ([i (range (length edges))])
                 (let* ([edge (list-ref edges i)]
                        [next (cond [(= (first edge) node) (second edge)]
                                    [(= (second edge) node) (first edge)] [else #f])])
                  (if (or (not next) (member next visited) (member next (second state))) #f
                   (list (+ (first state) (if (eq? metric 'fewest_edges) 1 (length (third edge))))
                         (append (second state) (list next))
                         (append (third state) (list i)))))))])
               (loop (append (rest ordered) more) (cons node visited)))])))))
   (define painted-pipes
    (for/fold ([out g]) ([i (third route)]) (paint-cells out (third (list-ref edges i)) 5)))
   (for/fold ([out painted-pipes]) ([i (second route)])
    (if (member i endpoints) out (paint-cells out (obj-cells (list-ref nodes i)) 3))))))
