(rule!
 ;; Fill enclosed background pockets selected by marker-adjacent indicator chains.
 ;; A marker is a singleton color. Its directly adjacent path/indicator color points
 ;; toward framed background pockets. Frame colors are inferred structurally from
 ;; colors adjacent to indicators (with a pure-enclosure test for alternates), so
 ;; outer walls and contaminating tokens do not become frames. Multiple singleton
 ;; markers independently color the pockets reached by their clean indicator chain.
 (lambda (g)
  (let ()
   (define H (rows g))
   (define W (cols g))
   (define D cardinal-deltas)
   (define (inside? p) (and (<= 0 (first p)) (< (first p) H) (<= 0 (second p)) (< (second p) W)))
   (define (nbrs p)
    (filter inside? (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) D)))
   (define colors (remove-duplicates (flatten g)))
   (define (freq v) (count-color g v))
   (define (most-common xs)
    (if (null? xs) #f
     (car (sort (remove-duplicates xs)
                (lambda (a b) (let ((ca (count (lambda (x) (= x a)) xs))
                                     (cb (count (lambda (x) (= x b)) xs)))
                                 (if (= ca cb) (< a b) (> ca cb))))))))
   (define bg (car (sort colors (lambda (a b) (> (freq a) (freq b))))))
   (define markers (sort (filter (lambda (v) (and (not (= v bg)) (= (freq v) 1))) colors) <))
   (define (cells-of v) (find-color g v))
   (define (indicator-for m)
    (let* ((p (first (cells-of m)))
           (vals (filter (lambda (v) (and (not (= v bg)) (not (member v markers))))
                         (map (lambda (q) (at g (first q) (second q))) (nbrs p)))))
     (most-common vals)))
   (define marker-info (map (lambda (m) (list m (indicator-for m))) markers))
   (define indicators (remove-duplicates (filter identity (map second marker-info))))
   (define excluded (append (list bg) markers indicators))
   (define (component start v)
    (let loop ((todo (list start)) (seen '()))
     (if (null? todo) seen
      (let* ((p (car todo)) (rest (cdr todo)))
       (if (member p seen)
        (loop rest seen)
        (let ((more (filter (lambda (q) (and (= (at g (first q) (second q)) v)
                                             (not (member q seen)))) (nbrs p))))
         (loop (append rest more) (cons p seen))))))))
   (define (components-of v)
    (let loop ((left (cells-of v)) (out '()))
     (if (null? left) (reverse out)
      (let* ((c (component (car left) v))
             (remain (filter (lambda (p) (not (member p c))) left)))
       (loop remain (cons c out))))))
   (define bg-components (components-of bg))
   (define (boundary comp)
    (let ((S comp))
     (remove-duplicates
      (apply append
       (map (lambda (p) (filter (lambda (q) (not (member q S))) (nbrs p))) comp)))))
   (define fsadj
    (apply append
     (for/list ((va indicators))
      (apply append
       (for/list ((p (cells-of va)))
        (filter (lambda (v) (not (member v excluded)))
                (map (lambda (q) (at g (first q) (second q))) (nbrs p))))))))
   (define candidates
    (if (null? fsadj)
     (filter (lambda (v) (not (member v excluded))) colors)
     fsadj))
   (define fdom (most-common candidates))
   (define (pure-frame? v)
    (ormap (lambda (comp)
            (let ((b (boundary comp)))
             (and (not (null? b)) (andmap (lambda (p) (= (at g (first p) (second p)) v)) b))))
           bg-components))
   (define fothers
    (if fdom
     (filter (lambda (v) (and (not (= v fdom)) (pure-frame? v))) (remove-duplicates candidates))
     '()))
   (define frames (if fdom (cons fdom fothers) '()))
   (define vdec
    (remove-duplicates
     (append (filter (lambda (v) (not (member v (append (list bg) markers indicators frames)))) colors)
             (filter (lambda (v) (not (member v frames))) (remove-duplicates candidates)))))
   (define pockets
    (filter (lambda (comp)
             (let ((b (boundary comp)))
              (and (not (null? frames)) (not (null? b))
                   (andmap (lambda (p) (member (at g (first p) (second p)) frames)) b))))
            bg-components))
   (define (chain-contaminated? va start)
    (let loop ((todo (list start)) (seen '()))
     (cond
      ((null? todo) #f)
      ((member (car todo) seen) (loop (cdr todo) seen))
      (else
       (let* ((p (car todo)) (ns (nbrs p)))
        (if (ormap (lambda (q) (member (at g (first q) (second q)) vdec)) ns) #t
         (loop (append (cdr todo)
                       (filter (lambda (q) (and (= (at g (first q) (second q)) va)
                                                (not (member q seen)))) ns))
               (cons p seen))))))))
   (define (clean? comp va)
    (ormap
     (lambda (fp)
      (ormap (lambda (q) (and (= (at g (first q) (second q)) va)
                              (not (chain-contaminated? va q))))
             (nbrs fp)))
     (filter (lambda (p) (member (at g (first p) (second p)) frames)) (boundary comp))))
   (define (rect? comp)
    (let* ((rs (map first comp)) (cs (map second comp))
           (r0 (apply min rs)) (r1 (apply max rs)) (c0 (apply min cs)) (c1 (apply max cs)))
     (= (length comp) (* (+ 1 (- r1 r0)) (+ 1 (- c1 c0))))))
   (define targets
    (if (and (= (length markers) 1) (not (null? fothers)))
     (filter-map
      (lambda (comp)
       (let ((exclusive (andmap (lambda (p) (= (at g (first p) (second p)) fdom)) (boundary comp))))
        (if (and (rect? comp) exclusive) #f (list comp (first markers))))) pockets)
     (let* ((assigned
             (filter-map
              (lambda (comp)
               (let loop ((mi marker-info))
                (cond ((null? mi) #f)
                      ((and (second (car mi)) (clean? comp (second (car mi)))) (list comp (first (car mi))))
                      (else (loop (cdr mi)))))) pockets))
            (any? (not (null? assigned))))
      (if any? assigned (map (lambda (comp) (list comp (first markers))) pockets)))))
   (for/fold ((out g)) ((item targets))
    (paint-cells out (first item) (second item))))))
