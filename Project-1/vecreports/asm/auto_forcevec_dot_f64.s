; auto_forcevec dot f64: largest loop body (10 instr)
ldp	q4, q5, [x9, #-0x20]
ldp	q6, q7, [x9], #0x40
ldp	q16, q17, [x10, #-0x20]
ldp	q18, q19, [x10], #0x40
fmla.2d	v1, v16, v4
fmla.2d	v0, v17, v5
fmla.2d	v2, v18, v6
fmla.2d	v3, v19, v7
subs	x11, x11, #0x8
b.ne	0x48 <ltmp0+0x48>
