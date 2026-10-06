; auto_forcevec saxpy_s4 f32: largest loop body (13 instr)
ld4.4s	{ v1, v2, v3, v4 }, [x10], #64
add	x13, x12, #0x10
ld4.4s	{ v16, v17, v18, v19 }, [x11], #64
add	x14, x12, #0x20
add	x15, x12, #0x30
fmla.4s	v16, v1, v0[0]
str	s16, [x12]
st1.s	{ v16 }[1], [x13]
st1.s	{ v16 }[2], [x14]
st1.s	{ v16 }[3], [x15]
mov	x12, x11
subs	x9, x9, #0x4
b.ne	0x38 <ltmp0+0x38>
