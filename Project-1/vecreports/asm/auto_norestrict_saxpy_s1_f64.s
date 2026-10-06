; auto_norestrict saxpy_s1 f64: largest loop body (31 instr) [truncated to 24]
lsl	x10, x8, #3
add	x9, x1, x10
add	x10, x2, x10
sub	x8, x0, x8
ldr	d1, [x9], #0x8
ldr	d2, [x10]
fmadd	d1, d0, d1, d2
str	d1, [x10], #0x8
subs	x8, x8, #0x1
b.ne	0x3c <ltmp0+0x3c>
movi.2d	v0, #0000000000000000
ret
and	x8, x0, #0xfffffffffffffff8
add	x9, x1, #0x20
add	x10, x2, #0x20
mov	x11, x8
ldp	q1, q2, [x9, #-0x20]
ldp	q3, q4, [x9], #0x40
ldp	q5, q6, [x10, #-0x20]
ldp	q7, q16, [x10]
fmla.2d	v5, v1, v0[0]
fmla.2d	v6, v2, v0[0]
fmla.2d	v7, v3, v0[0]
fmla.2d	v16, v4, v0[0]
