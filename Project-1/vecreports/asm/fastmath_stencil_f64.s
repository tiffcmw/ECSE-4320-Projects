; fastmath stencil f64: largest loop body (24 instr)
ldp	q3, q4, [x13, #-0x20]
ldp	q5, q6, [x13]
ext.16b	v7, v0, v4, #0x8
ldr	q0, [x13, #0x20]
ext.16b	v16, v4, v5, #0x8
ext.16b	v17, v5, v6, #0x8
ext.16b	v18, v6, v0, #0x8
fmul.2d	v7, v7, v1
fmul.2d	v16, v16, v1
fmul.2d	v17, v17, v1
fmul.2d	v18, v18, v1
fadd.2d	v3, v4, v3
fadd.2d	v4, v5, v4
fadd.2d	v5, v6, v5
fadd.2d	v6, v0, v6
fmla.2d	v7, v3, v2
fmla.2d	v16, v4, v2
fmla.2d	v17, v5, v2
stp	q7, q16, [x12, #-0x20]
fmla.2d	v18, v6, v2
stp	q17, q18, [x12], #0x40
add	x13, x13, #0x40
subs	x14, x14, #0x8
b.ne	0x48 <ltmp0+0x48>
