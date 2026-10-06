; fastmath gather f32: largest loop body (14 instr)
ldp	w12, w13, [x9, #-0x8]
ldp	w14, w15, [x9], #0x10
add	x13, x1, x13, lsl #2
add	x14, x1, x14, lsl #2
add	x15, x1, x15, lsl #2
ldr	s1, [x1, x12, lsl #2]
ld1.s	{ v1 }[1], [x13]
ld1.s	{ v1 }[2], [x14]
ld1.s	{ v1 }[3], [x15]
ldr	q2, [x10]
fmla.4s	v2, v1, v0[0]
str	q2, [x10], #0x10
subs	x11, x11, #0x4
b.ne	0x28 <ltmp0+0x28>
