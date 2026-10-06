; auto_norestrict saxpy_s1 u32: largest loop body (53 instr) [truncated to 24]
lsl	x11, x9, #2
add	x10, x1, x11
add	x11, x2, x11
sub	x9, x0, x9
ldr	w12, [x10], #0x4
ldr	w13, [x11]
madd	w12, w12, w8, w13
str	w12, [x11], #0x4
subs	x9, x9, #0x1
b.ne	0x40 <ltmp0+0x40>
movi.2d	v0, #0000000000000000
ret
cmp	x0, #0x10
b.hs	0x70 <ltmp0+0x70>
mov	x9, #0x0                ; =0
b	0xc4 <ltmp0+0xc4>
and	x9, x0, #0xfffffffffffffff0
fmov	s0, w8
add	x10, x1, #0x20
add	x11, x2, #0x20
mov	x12, x9
ldp	q1, q2, [x10, #-0x20]
ldp	q3, q4, [x10], #0x40
ldp	q5, q6, [x11, #-0x20]
