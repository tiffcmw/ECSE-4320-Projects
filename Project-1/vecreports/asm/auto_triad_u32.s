; auto triad u32: largest loop body (12 instr)
ldp	q1, q2, [x10, #-0x20]
ldp	q3, q4, [x10], #0x40
ldp	q5, q6, [x11, #-0x20]
ldp	q7, q16, [x11], #0x40
mla.4s	v1, v5, v0[0]
mla.4s	v2, v6, v0[0]
mla.4s	v3, v7, v0[0]
mla.4s	v4, v16, v0[0]
stp	q1, q2, [x12, #-0x20]
stp	q3, q4, [x12], #0x40
subs	x13, x13, #0x10
b.ne	0x40 <ltmp0+0x40>
