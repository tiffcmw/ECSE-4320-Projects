; auto gather u32: largest loop body (14 instr)
ldp	w13, w14, [x10, #-0x8]
ldp	w15, w16, [x10], #0x10
add	x14, x1, x14, lsl #2
add	x15, x1, x15, lsl #2
add	x16, x1, x16, lsl #2
ldr	s1, [x1, x13, lsl #2]
ld1.s	{ v1 }[1], [x14]
ld1.s	{ v1 }[2], [x15]
ld1.s	{ v1 }[3], [x16]
ldr	q2, [x11]
mla.4s	v2, v1, v0[0]
str	q2, [x11], #0x10
subs	x12, x12, #0x4
b.ne	0x2c <ltmp0+0x2c>
