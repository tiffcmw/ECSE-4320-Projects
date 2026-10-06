; native stencil u32: largest loop body (27 instr) [truncated to 24]
ldp	q1, q2, [x13, #-0x20]
ldp	q3, q4, [x13]
ldur	q5, [x13, #-0x18]
ldur	q6, [x13, #-0x8]
ldur	q7, [x13, #0x8]
ext.16b	v16, v0, v5, #0xc
ldur	q0, [x13, #0x18]
ext.16b	v17, v5, v6, #0xc
ext.16b	v18, v6, v7, #0xc
ext.16b	v19, v7, v0, #0xc
add.4s	v16, v16, v16
add.4s	v17, v17, v17
add.4s	v18, v18, v18
add.4s	v19, v19, v19
add.4s	v1, v1, v5
add.4s	v1, v16, v1
add.4s	v2, v2, v6
add.4s	v2, v17, v2
add.4s	v3, v3, v7
add.4s	v3, v18, v3
add.4s	v4, v4, v0
stp	q1, q2, [x12, #-0x20]
add.4s	v1, v19, v4
stp	q3, q1, [x12], #0x40
