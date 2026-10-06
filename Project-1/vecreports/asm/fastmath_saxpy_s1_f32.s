; fastmath saxpy_s1 f32: largest loop body (12 instr)
ldp	q1, q2, [x9, #-0x20]
ldp	q3, q4, [x9], #0x40
ldp	q5, q6, [x10, #-0x20]
ldp	q7, q16, [x10]
fmla.4s	v5, v1, v0[0]
fmla.4s	v6, v2, v0[0]
fmla.4s	v7, v3, v0[0]
fmla.4s	v16, v4, v0[0]
stp	q5, q6, [x10, #-0x20]
stp	q7, q16, [x10], #0x40
subs	x11, x11, #0x10
b.ne	0x38 <ltmp0+0x38>
