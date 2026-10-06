; fastmath gather f64: largest loop body (15 instr)
ldp	w12, w13, [x9, #-0x8]
ldp	w14, w15, [x9], #0x10
add	x13, x1, x13, lsl #3
add	x15, x1, x15, lsl #3
ldr	d1, [x1, x12, lsl #3]
ld1.d	{ v1 }[1], [x13]
ldp	q2, q3, [x10, #-0x10]
fmla.2d	v2, v1, v0[0]
ldr	d1, [x1, x14, lsl #3]
ld1.d	{ v1 }[1], [x15]
fmla.2d	v3, v1, v0[0]
stp	q2, q3, [x10, #-0x10]
add	x10, x10, #0x20
subs	x11, x11, #0x4
b.ne	0x24 <ltmp0+0x24>
