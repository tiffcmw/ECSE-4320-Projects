; auto_forcevec gather f64: largest loop body (10 instr)
ldp	w12, w13, [x9, #-0x4]
add	x13, x1, x13, lsl #3
ldr	d1, [x1, x12, lsl #3]
ld1.d	{ v1 }[1], [x13]
ldr	q2, [x11]
fmla.2d	v2, v1, v0[0]
str	q2, [x11], #0x10
add	x9, x9, #0x8
subs	x10, x10, #0x2
b.ne	0x24 <ltmp0+0x24>
