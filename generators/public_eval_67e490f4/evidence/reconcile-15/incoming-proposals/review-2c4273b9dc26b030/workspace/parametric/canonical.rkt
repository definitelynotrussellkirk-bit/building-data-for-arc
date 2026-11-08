(rule!
 ;; The largest monochrome 4-connected object is a tableau. Its enclosed
 ;; background components are shape slots. Monochrome components outside the
 ;; tableau are votes: compare shape up to translation, rotation and reflection.
 ;; Fill every slot with the color having the most matching outside components,
 ;; then crop to the tableau bounding box.
 (lambda (g)
  (let ()
   (define match-mode "dihedral")
   (define bg (mode g -1))
   (define dirs '((1 0) (-1 0) (0 1) (0 -1)))
   (define occupied (filter (lambda (p) (!= (at g (first p) (second p)) bg)) (grid-positions g)))
   (define (same-component p)
    (define color (at g (first p) (second p)))
    (connected-region g (first p) (second p) (lambda (r c v) (= v color)) 4))
   (define (components cells)
    (let loop ([remaining cells] [out '()])
     (if (null? remaining) (reverse out)
      (let* ([part (same-component (first remaining))]
             [left (filter (lambda (p) (not (member p part))) remaining)])
       (loop left (cons part out))))))
   (define comps (components occupied))
   (define main (pick-max comps length))
   (define box (bbox-of-cells main))
   (define r0 (first box)) (define c0 (second box)) (define r1 (third box)) (define c1 (fourth box))
   (define (inside? p) (and (<= r0 (first p) r1) (<= c0 (second p) c1)))
   (define (normalize cells)
    (let* ([mr (apply min (map first cells))] [mc (apply min (map second cells))])
     (sort (map (lambda (p) (list (- (first p) mr) (- (second p) mc))) cells)
           (lambda (a b) (or (< (first a) (first b)) (and (= (first a) (first b)) (< (second a) (second b))))))))
   (define (rot p) (list (second p) (- (first p))))
   (define (flip p) (list (first p) (- (second p))))
   (define (apply-n f p n) (if (= n 0) p (apply-n f (f p) (- n 1))))
   (define (equiv? a b)
    (if (equal? match-mode "translation_only")
        (equal? (normalize a) (normalize b))
        (ormap (lambda (fl)
          (ormap (lambda (n)
            (equal? (normalize a)
                    (normalize (map (lambda (p) (apply-n rot (if fl (flip p) p) n)) b))))
           '(0 1 2 3))) '(#f #t))))
   (define outside (filter (lambda (part) (and (not (equal? part main)) (andmap (lambda (p) (not (inside? p))) part))) comps))
   ;; Find enclosed background components inside the tableau box.
   (define bg-inside (filter (lambda (p) (and (inside? p) (= (at g (first p) (second p)) bg))) (grid-positions g)))
   (define (bg-region p)
    (connected-region g (first p) (second p) (lambda (r c v) (and (= v bg) (<= r0 r r1) (<= c0 c c1))) 4))
   (define holes
    (let loop ([remaining bg-inside] [out '()])
     (if (null? remaining) (reverse out)
      (let* ([part (bg-region (first remaining))]
             [left (filter (lambda (p) (not (member p part))) remaining)]
             [touch (ormap (lambda (p) (or (= (first p) r0) (= (first p) r1) (= (second p) c0) (= (second p) c1))) part)])
       (loop left (if touch out (cons part out)))))))
   ;; A: derive the input-dependent winner color for each hole shape.
   (define hole-winners
    (for/list ([hole (in-list holes)])
     (let* ([matches (filter (lambda (part) (equiv? hole part)) outside)]
            [colors (remove-duplicates (map (lambda (part) (at g (first (first part)) (second (first part)))) matches))]
            [winner (if (null? colors) bg
                     (pick-max colors (lambda (color)
                       (count-if (lambda (part) (= (at g (first (first part)) (second (first part))) color)) matches))))])
      (list hole winner))))
   ;; B consumes A's vote table and paints the slots before cropping.
   (define painted
    (for/fold ([out g]) ([rec (in-list hole-winners)])
     (recolor-cells out (first rec) (second rec))))
   (build-grid (+ 1 (- r1 r0)) (+ 1 (- c1 c0)) (r c) (at painted (+ r r0) (+ c c0))))))
