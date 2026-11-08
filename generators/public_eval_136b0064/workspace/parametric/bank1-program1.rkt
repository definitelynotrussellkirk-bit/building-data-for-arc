(rule!
 ;; Decode colored 3x3 instructions on the left of the yellow divider.
 ;; Read row major; 1=right3, 2=left2, 3=left4, 6=down2.
 ;; Start below the gray marker and thread the endpoint through every stroke.
 ;; Horizontal strokes include the entry column. The right canvas is the output.
 (lambda (g)
  (let ()
   (define wall (first (filter (lambda (c) (for/and ((r (range (rows g)))) (= (at g r c) 4))) (range (cols g)))))
   (define canvas (subgrid g 0 (+ wall 1) (- (rows g) 1) (- (cols g) 1)))
   (define glyphs (filter (lambda (o) (< (obj-c2 o) wall)) (objects-8 g 0)))
   (define ordered (sort glyphs (lambda (a b) (if (= (obj-r1 a) (obj-r1 b)) (< (obj-c1 a) (obj-c1 b)) (< (obj-r1 a) (obj-r1 b))))))
   (define codes (map obj-color ordered))
   (define start (first (find-color canvas 5)))
   (define result
    (for/fold ((state (list canvas (first start) (second start)))) ((color codes))
     (let* ((out (first state)) (r (second state)) (c (third state))
            (n (cond ((= color 1) 3) ((= color 2) 2) ((= color 3) 4) (else 2)))
            (direction (cond ((= color 1) 1) ((= color 6) 0) (else -1)))
            (cells (for/list ((j (range n)))
                     (if (= direction 0) (list (+ r 1 j) c)
                       (list (+ r 1) (+ c (* direction (+ j 0)))))))
            (painted (for/fold ((a out)) ((p cells))
                       (if (in-bounds? (first p) (second p) (rows out) (cols out))
                         (set-cell a (first p) (second p) color) a)))
            (endpoint (last cells)))
       (list painted (first endpoint) (second endpoint)))))
   (first result))))
