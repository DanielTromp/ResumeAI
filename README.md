#   R e s u m e A I   -   R e s u m e   &   V a c a n c y   M a t c h i n g   S y s t e m 
 
 A   f u l l - s t a c k   a p p l i c a t i o n   t h a t   a u t o m a t i c a l l y   s c r a p e s   j o b   v a c a n c i e s ,   s t o r e s   t h e m   i n   a   d a t a b a s e ,   a n d   m a t c h e s   t h e m   w i t h   r e s u m e s   u s i n g   A I . 
 
 # #   P r o j e c t   S t r u c t u r e 
 
 -   * * b a c k e n d / * *   -   F a s t A P I   b a c k e n d 
     -   * * a p p / * *   -   B a c k e n d   a p p l i c a t i o n   c o d e 
         -   * * c o m p o n e n t s / * *   -   S h a r e d   c o m p o n e n t s   ( N o c o D B   c l i e n t ,   e t c . ) 
         -   * * d a t a b a s e / * *   -   D a t a b a s e   i n t e r f a c e s   ( S Q L i t e ,   N o c o D B ) 
         -   * * m o d e l s / * *   -   P y d a n t i c   d a t a   m o d e l s 
         -   * * r o u t e r s / * *   -   A P I   r o u t e   d e f i n i t i o n s 
         -   * * s e r v i c e s / * *   -   B u s i n e s s   l o g i c   s e r v i c e s 
         -   * * r e s u m e s / * *   -   P D F   r e s u m e   s t o r a g e 
     -   * * m a i n . p y * *   -   F a s t A P I   a p p l i c a t i o n   e n t r y   p o i n t 
     -   * * r e q u i r e m e n t s . t x t * *   -   B a c k e n d   d e p e n d e n c i e s 
 
 -   * * f r o n t e n d / * *   -   R e a c t   f r o n t e n d 
     -   * * s r c / * *   -   R e a c t   s o u r c e   c o d e 
         -   * * c o m p o n e n t s / * *   -   R e u s a b l e   U I   c o m p o n e n t s 
         -   * * p a g e s / * *   -   P a g e   c o m p o n e n t s 
         -   * * A p p . j s * *   -   M a i n   R e a c t   c o m p o n e n t 
         -   * * i n d e x . j s * *   -   R e a c t   e n t r y   p o i n t 
 
 # #   F e a t u r e s 
 
 -   S c r a p e   j o b   l i s t i n g s   f r o m   S p i n w e b 
 -   S t o r e   v a c a n c i e s   i n   N o c o D B   o r   S Q L i t e 
 -   P r o c e s s   r e s u m e s   a n d   g e n e r a t e   e m b e d d i n g s 
 -   M a t c h   v a c a n c i e s   w i t h   r e s u m e s   u s i n g   v e c t o r   s i m i l a r i t y 
 -   E v a l u a t e   m a t c h e s   u s i n g   O p e n A I   G P T - 4 o - m i n i 
 -   I n t e r a c t i v e   w e b   d a s h b o a r d   t o   v i e w   a n d   m a n a g e   v a c a n c i e s   a n d   r e s u m e s 
 
 # #   S e t u p 
 
 # # #   B a c k e n d 
 
 1 .   C r e a t e   a n d   a c t i v a t e   a   v i r t u a l   e n v i r o n m e n t : 
 ` ` ` b a s h 
 #   W i n d o w s 
 p y t h o n   - m   v e n v   v e n v 
 . \ v e n v \ S c r i p t s \ a c t i v a t e 
 
 #   L i n u x / m a c O S 
 p y t h o n 3   - m   v e n v   v e n v 
 s o u r c e   v e n v / b i n / a c t i v a t e 
 ` ` ` 
 
 2 .   I n s t a l l   t h e   r e q u i r e d   p a c k a g e s : 
 ` ` ` b a s h 
 c d   b a c k e n d 
 p i p   i n s t a l l   - r   r e q u i r e m e n t s . t x t 
 ` ` ` 
 
 3 .   I n s t a l l   P l a y w r i g h t   b r o w s e r s : 
 ` ` ` b a s h 
 p l a y w r i g h t   i n s t a l l 
 ` ` ` 
 
 4 .   S e t   u p   y o u r   e n v i r o n m e n t   v a r i a b l e s   b y   c o p y i n g   ` . e n v . e x a m p l e `   t o   ` . e n v ` : 
 ` ` ` b a s h 
 c p   . e n v . e x a m p l e   . e n v 
 ` ` ` 
 
 5 .   U p d a t e   t h e   ` . e n v `   f i l e   w i t h   y o u r   c r e d e n t i a l s   a n d   c o n f i g u r a t i o n 
 
 6 .   R u n   t h e   b a c k e n d   s e r v e r : 
 ` ` ` b a s h 
 c d   b a c k e n d 
 u v i c o r n   m a i n : a p p   - - r e l o a d 
 ` ` ` 
 
 # # #   F r o n t e n d 
 
 1 .   I n s t a l l   d e p e n d e n c i e s : 
 ` ` ` b a s h 
 c d   f r o n t e n d 
 n p m   i n s t a l l 
 ` ` ` 
 
 2 .   S t a r t   t h e   d e v e l o p m e n t   s e r v e r : 
 ` ` ` b a s h 
 n p m   s t a r t 
 ` ` ` 
 
 # #   A P I   E n d p o i n t s 
 
 -   ` G E T   / a p i / v a c a n c i e s `   -   G e t   a l l   v a c a n c i e s   w i t h   p a g i n a t i o n 
 -   ` G E T   / a p i / v a c a n c i e s / { i d } `   -   G e t   a   s p e c i f i c   v a c a n c y 
 -   ` P O S T   / a p i / v a c a n c i e s `   -   C r e a t e   a   n e w   v a c a n c y 
 -   ` P U T   / a p i / v a c a n c i e s / { i d } `   -   U p d a t e   a   v a c a n c y 
 -   ` D E L E T E   / a p i / v a c a n c i e s / { i d } `   -   D e l e t e   a   v a c a n c y 
 -   ` G E T   / a p i / r e s u m e s `   -   G e t   a l l   r e s u m e s 
 -   ` G E T   / a p i / r e s u m e s / { i d } `   -   G e t   a   s p e c i f i c   r e s u m e 
 -   ` P O S T   / a p i / r e s u m e s `   -   A d d   a   r e s u m e   f r o m   J S O N 
 -   ` P O S T   / a p i / r e s u m e s / u p l o a d `   -   U p l o a d   a   r e s u m e   P D F   f i l e 
 -   ` G E T   / a p i / s e t t i n g s `   -   G e t   a p p l i c a t i o n   s e t t i n g s 
 -   ` P U T   / a p i / s e t t i n g s `   -   U p d a t e   a p p l i c a t i o n   s e t t i n g s 
 
 # #   D a t a b a s e   C o n f i g u r a t i o n 
 
 T h e   s y s t e m   s u p p o r t s   m u l t i p l e   d a t a b a s e   b a c k e n d s : 
 
 1 .   * * S Q L i t e * *   -   S i m p l e   f i l e - b a s e d   d a t a b a s e   ( d e f a u l t ) 
       -   S e t   ` D B _ T Y P E = s q l i t e `   i n   ` . e n v ` 
       -   S e t   ` S Q L I T E _ D B _ P A T H = p a t h / t o / d a t a b a s e . d b `   i n   ` . e n v ` 
 
 2 .   * * N o c o D B * *   -   W e b - b a s e d   d a t a b a s e   w i t h   A i r t a b l e - l i k e   U I 
       -   S e t   ` D B _ T Y P E = n o c o d b `   i n   ` . e n v ` 
       -   C o n f i g u r e   N o c o D B   c r e d e n t i a l s   i n   ` . e n v ` 
 
 # #   O r i g i n a l   C L I - B a s e d   S y s t e m 
 
 T h e   o r i g i n a l   C L I - b a s e d   s y s t e m   i s   s t i l l   a v a i l a b l e   i n   t h e   f o l l o w i n g   d i r e c t o r i e s : 
 -   * * 0 1 _ O A S / * *   -   O p e n A I   R e s u m e   M a t c h i n g   S y s t e m   ( A i r t a b l e   V e r s i o n ) 
 -   * * 0 2 _ O C L / * *   -   O p e n A I   R e s u m e   M a t c h i n g   S y s t e m   ( L o c a l   V e r s i o n ) 
 -   * * 0 3 _ O N S / * *   -   O p e n A I   R e s u m e   M a t c h i n g   S y s t e m   ( N o c o D B   V e r s i o n ) 
 
 T o   u s e   t h e   o r i g i n a l   s y s t e m : 
 ` ` ` b a s h 
 c d   0 3 _ O N S 
 p y t h o n   c o m b i n e d _ p r o c e s s . p y 
 ` ` ` 
 
 # #   T r o u b l e s h o o t i n g 
 
 -   F o r   P l a y w r i g h t   e r r o r s ,   t r y   r e i n s t a l l i n g   t h e   b r o w s e r s : 
 ` ` ` b a s h 
 p l a y w r i g h t   i n s t a l l 
 ` ` ` 
 
 -   F o r   N o c o D B   e r r o r s ,   c h e c k   i f : 
     -   Y o u r   A P I   t o k e n   i s   c o r r e c t 
     -   T h e   U R L ,   p r o j e c t ,   a n d   t a b l e   n a m e s   a r e   c o r r e c t 
     -   T h e   f i e l d   n a m e s   a r e   c o r r e c t   ( c a s e - s e n s i t i v e ) 
 
 -   F o r   O p e n A I   e r r o r s ,   c h e c k   i f : 
     -   Y o u r   A P I   k e y   i s   c o r r e c t 
     -   Y o u   h a v e   s u f f i c i e n t   c r e d i t s 
 
 # #   A u t h o r 
 
 -   * * D a n i e l   T r o m p * * 
 -   * * E m a i l : * *   d r p g m t r o m p @ g m a i l . c o m 
 -   * * V e r s i o n : * *   2 . 0 . 0 
 -   * * L i c e n s e : * *   M I T 
 -   * * R e p o s i t o r y : * *   h t t p s : / / g i t h u b . c o m / D a n i e l T r o m p / R e s u m e A I 