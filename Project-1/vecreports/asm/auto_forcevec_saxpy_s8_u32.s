; auto_forcevec saxpy_s8 u32: largest loop body (27 instr) [truncated to 24]
ldr	q1, [x11, #0x60]
ldr	q2, [x11, #0x40]
ldr	q3, [x11, #0x20]
ldr	q4, [x11], #0x80
zip1.4s	v3, v4, v3
zip1.4s	v1, v2, v1
ext.16b	v1, v2, v1, #0x8
mov.d	v3[1], v1[1]
add	x13, x12, #0x40
ldr	q1, [x12, #0x60]
ldr	q2, [x12, #0x40]
ldr	q4, [x12, #0x20]
ldr	q5, [x12]
zip1.4s	v4, v5, v4
zip1.4s	v1, v2, v1
ext.16b	v1, v2, v1, #0x8
mov.d	v4[1], v1[1]
add	x14, x12, #0x60
mla.4s	v4, v3, v0[0]
str	s4, [x12]
mov	s1, v4[1]
st1.s	{ v4 }[2], [x13]
str	s1, [x12, #0x20]
st1.s	{ v4 }[3], [x14]
