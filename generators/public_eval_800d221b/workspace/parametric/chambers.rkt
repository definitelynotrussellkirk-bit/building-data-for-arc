(rule!
 ;; The modal background surrounds a spatially spanning wire network.
 ;; Its unique solid 3x3 hub joins mixed-color terminal chambers. Remove the
 ;; hub to recover the terminals; each terminal's pigment majority colors its
 ;; own wires. The hub center takes a second majority, counting the recovered
 ;; terminal value once per chamber, irrespective of its number of wire contacts.
 ;; All original pigments and the other eight hub cells remain unchanged.
 ;; Lower colors break vote ties; generated lessons exclude all such ties.
 (lambda (g)
   (let ()
     (define (mode-color xs)
       (pick-max (sort (remove-duplicates xs) <)
                 (lambda (v) (count-if (lambda (x) (= x v)) xs))))
     (define bg (mode-color (apply append g)))
     (define network
       (pick-max (objects g bg) (lambda (o) (* (obj-h o) (obj-w o)))))
     (define wire (obj-color network))
     (define centers
       (for*/list ([r (range 1 (- h 1))] [c (range 1 (- w 1))]
                   #:when (for*/and ([dr '(-1 0 1)] [dc '(-1 0 1)])
                            (= (at g (+ r dr) (+ c dc)) wire)))
         (list r c)))
     (define center (first centers))
     (define hr (first center))
     (define hc (second center))
     (define (in-hub? r c)
       (and (<= (- hr 1) r (+ hr 1)) (<= (- hc 1) c (+ hc 1))))
     (define mask
       (for/list ([r (range h)])
         (for/list ([c (range w)])
           (if (or (in-hub? r c) (= (at g r c) bg)) bg wire))))
     (define terminals
       (for/list ([o (objects mask bg)])
         (let ()
           (define cells (obj-cells o))
           (define pigments
             (for/list ([p cells] #:when (not (= (at g (first p) (second p)) wire)))
               (at g (first p) (second p))))
           (define local-vote (mode-color pigments))
           (define contacts
             (for/sum ([p cells])
               (let ([r (first p)] [c (second p)])
                 (if (and (= (at g r c) wire)
                          (or (in-hub? (- r 1) c) (in-hub? (+ r 1) c)
                              (in-hub? r (- c 1)) (in-hub? r (+ c 1)))) 1 0))))
           (list cells local-vote contacts))))
     (define votes
       (apply append
         (for/list ([terminal terminals])
           (make-list 1 (second terminal)))))
     (define propagated
       (for/fold ([out g]) ([terminal terminals])
         (for/fold ([result out]) ([p (first terminal)])
           (if (= (at g (first p) (second p)) wire)
               (set-cell result (first p) (second p) (second terminal)) result))))
     (set-cell propagated hr hc (mode-color votes)))))
