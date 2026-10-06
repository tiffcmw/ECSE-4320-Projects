; auto dot f64: largest loop body (22 instr)
ldp	q1, q2, [x9, #-0x20]
ldp	q3, q4, [x9], #0x40
ldp	q5, q6, [x10, #-0x20]
ldp	q7, q16, [x10], #0x40
fmul.2d	v1, v1, v5
mov	d5, v1[1]
fmul.2d	v2, v2, v6
mov	d6, v2[1]
fmul.2d	v3, v3, v7
mov	d7, v3[1]
fmul.2d	v4, v4, v16
mov	d16, v4[1]
fadd	d0, d0, d1
fadd	d0, d0, d5
fadd	d0, d0, d2
fadd	d0, d0, d6
fadd	d0, d0, d3
fadd	d0, d0, d7
fadd	d0, d0, d4
fadd	d0, d0, d16
subs	x11, x11, #0x8
b.ne	0x34 <ltmp0+0x34>
