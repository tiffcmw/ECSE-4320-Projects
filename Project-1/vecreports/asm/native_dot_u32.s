; native dot u32: largest loop body (10 instr)
ldp	q4, q5, [x9, #-0x20]
ldp	q6, q7, [x9], #0x40
ldp	q16, q17, [x10, #-0x20]
ldp	q18, q19, [x10], #0x40
mla.4s	v0, v16, v4
mla.4s	v1, v17, v5
mla.4s	v2, v18, v6
mla.4s	v3, v19, v7
subs	x11, x11, #0x10
b.ne	0x54 <ltmp0+0x54>
