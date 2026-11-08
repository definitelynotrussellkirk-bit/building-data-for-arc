(rule!
 ;; Four equal quadrants: top-left/top-right nonzero counts encode output
 ;; height/width. Bottom-right is a periodic stencil; zeros are transparent.
 ;; Find its smallest EXACT rectangular repeat (dividing the quadrant size).
 ;; Each primitive stencil copy takes its transparent color from the next
 ;; bottom-left backing cell. Repeat the backing as needed and crop to size.
 ;; The optional snake policy reverses addressing on odd backing rows.
 (lambda (g)
   (let ()
     (define backing-policy "raster")
     (define period-policy "primitive")
     (define qh (quotient (length g) 2))
     (define qw (quotient (length (first g)) 2))
     (define (get r c) (list-ref (list-ref g r) c))
     (define (tile r c) (get (+ qh r) (+ qw c)))
     (define oh (for*/sum ([r (range qh)] [c (range qw)]) (if (= (get r c) 0) 0 1)))
     (define ow (for*/sum ([r (range qh)] [c (range qw)]) (if (= (get r (+ qw c)) 0) 0 1)))
     (define ph
       (if (equal? period-policy "raw") qh
           (for/first ([p (range 1 (+ qh 1))]
                       #:when (and (= (modulo qh p) 0)
                         (for*/and ([r (range qh)] [c (range qw)])
                           (= (tile r c) (tile (modulo r p) c))))) p)))
     (define pw
       (if (equal? period-policy "raw") qw
           (for/first ([p (range 1 (+ qw 1))]
                       #:when (and (= (modulo qw p) 0)
                         (for*/and ([r (range qh)] [c (range qw)])
                           (= (tile r c) (tile r (modulo c p)))))) p)))
     (for/list ([r (range oh)])
       (for/list ([c (range ow)])
         (let* ([v (tile (modulo r ph) (modulo c pw))]
                [br (modulo (quotient r ph) qh)]
                [bc0 (modulo (quotient c pw) qw)]
                [bc (if (and (equal? backing-policy "snake") (odd? br)) (- qw 1 bc0) bc0)])
           (if (= v 0) (get (+ qh br) bc) v)))))))
