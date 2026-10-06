; fastmath mul u32: largest loop body (12 instr)
ldp	q0, q1, [x9, #-0x20]
ldp	q2, q3, [x9], #0x40
ldp	q4, q5, [x10, #-0x20]
ldp	q6, q7, [x10], #0x40
mul.4s	v0, v4, v0
mul.4s	v1, v5, v1
mul.4s	v2, v6, v2
mul.4s	v3, v7, v3
stp	q0, q1, [x11, #-0x20]
stp	q2, q3, [x11], #0x40
subs	x12, x12, #0x10
b.ne	0x38 <ltmp0+0x38>
