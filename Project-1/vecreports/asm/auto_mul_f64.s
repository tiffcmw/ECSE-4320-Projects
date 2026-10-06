; auto mul f64: largest loop body (12 instr)
ldp	q0, q1, [x9, #-0x20]
ldp	q2, q3, [x9], #0x40
ldp	q4, q5, [x10, #-0x20]
ldp	q6, q7, [x10], #0x40
fmul.2d	v0, v0, v4
fmul.2d	v1, v1, v5
fmul.2d	v2, v2, v6
fmul.2d	v3, v3, v7
stp	q0, q1, [x11, #-0x20]
stp	q2, q3, [x11], #0x40
subs	x12, x12, #0x8
b.ne	0x28 <ltmp0+0x28>
