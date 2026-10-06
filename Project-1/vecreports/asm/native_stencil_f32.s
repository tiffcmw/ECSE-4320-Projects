; native stencil f32: largest loop body (27 instr) [truncated to 24]
ldp	q3, q4, [x13, #-0x20]
ldp	q5, q6, [x13]
ldur	q7, [x13, #-0x18]
ldur	q16, [x13, #-0x8]
ldur	q17, [x13, #0x8]
ext.16b	v18, v2, v7, #0xc
ldur	q2, [x13, #0x18]
ext.16b	v19, v7, v16, #0xc
ext.16b	v20, v16, v17, #0xc
ext.16b	v21, v17, v2, #0xc
fmul.4s	v18, v18, v0
fmul.4s	v19, v19, v0
fmul.4s	v20, v20, v0
fmul.4s	v21, v21, v0
fmla.4s	v18, v1, v3
fmla.4s	v19, v1, v4
fmla.4s	v20, v1, v5
fmla.4s	v21, v1, v6
fmla.4s	v18, v1, v7
fmla.4s	v19, v1, v16
fmla.4s	v20, v1, v17
stp	q18, q19, [x12, #-0x20]
fmla.4s	v21, v1, v2
stp	q20, q21, [x12], #0x40
