(rule!
 ;; Infer the modal background. The layout is the unique foreground color whose
 ;; color neither touches another color nor overlaps its bounding box. Remaining
 ;; colors form the multicolor motif. Crop both tightly without rotating them.
 ;; Replace each occupied layout cell by the entire motif; an empty layout cell
 ;; produces an equally sized background tile. Preserve every motif color/hole.
 (lambda (g)
   (let ()
     (define bg (mode g -1))
     (define colors (filter (lambda (v) (not (= v bg))) (grid-colors g)))
     (define (cells v) (filter (lambda (p) (= (at g (first p) (second p)) v)) (grid-positions g)))
     (define (box v) (bbox-of-cells (cells v)))
     (define (disjoint a b) (or (< (third a) (first b)) (< (third b) (first a)) (< (fourth a) (second b)) (< (fourth b) (second a))))
     (define (touches a b)
       (ormap (lambda (p) (ormap (lambda (d) (member (list (+ (first p) (first d)) (+ (second p) (second d))) (cells b))) cardinal-deltas)) (cells a)))
     (define isolated (filter (lambda (v) (andmap (lambda (u) (or (= u v) (and (disjoint (box u) (box v)) (not (touches u v))))) colors)) colors))
     (define key (if (= (length isolated) 1) (first isolated) (error 'roles "Ambiguous layout color")))
     (define layout (apply subgrid (cons g (box key))))
     (define motif-cells (filter (lambda (p) (not (member (at g (first p) (second p)) (list bg key)))) (grid-positions g)))
     (define motif (apply subgrid (cons g (bbox-of-cells motif-cells))))
     (define ph (rows motif))
     (define pw (cols motif))
     (define expanded
       (grid-from-fn (* (rows layout) ph) (* (cols layout) pw)
         (lambda (r c) (if (= (at layout (quotient r ph) (quotient c pw)) key)
                            (at motif (remainder r ph) (remainder c pw)) bg))))
     expanded)))
