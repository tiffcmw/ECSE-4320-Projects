; auto_norestrict saxpy f32: largest loop body (51 instr) [truncated to 24]
lsl	x10, x8, #2
add	x9, x1, x10
add	x10, x2, x10
sub	x8, x0, x8
ldr	s1, [x9], #0x4
ldr	s2, [x10]
fmadd	s1, s0, s1, s2
str	s1, [x10], #0x4
subs	x8, x8, #0x1
b.ne	0x40 <ltmp0+0x40>
movi.2d	v0, #0000000000000000
ret
cmp	x0, #0x10
b.hs	0x70 <ltmp0+0x70>
mov	x8, #0x0                ; =0
b	0xc0 <ltmp0+0xc0>
and	x8, x0, #0xfffffffffffffff0
add	x9, x1, #0x20
add	x10, x2, #0x20
mov	x11, x8
ldp	q1, q2, [x9, #-0x20]
ldp	q3, q4, [x9], #0x40
ldp	q5, q6, [x10, #-0x20]
ldp	q7, q16, [x10]
