; auto saxpy u32: largest loop body (12 instr)
ldp	q1, q2, [x10, #-0x20]
ldp	q3, q4, [x10], #0x40
ldp	q5, q6, [x11, #-0x20]
ldp	q7, q16, [x11]
mla.4s	v5, v1, v0[0]
mla.4s	v6, v2, v0[0]
mla.4s	v7, v3, v0[0]
mla.4s	v16, v4, v0[0]
stp	q5, q6, [x11, #-0x20]
stp	q7, q16, [x11], #0x40
subs	x12, x12, #0x10
b.ne	0x3c <ltmp0+0x3c>
