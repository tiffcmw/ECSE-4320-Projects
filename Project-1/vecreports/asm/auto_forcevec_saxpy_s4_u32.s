; auto_forcevec saxpy_s4 u32: largest loop body (13 instr)
ld4.4s	{ v1, v2, v3, v4 }, [x11], #64
ld4.4s	{ v16, v17, v18, v19 }, [x12], #64
add	x14, x13, #0x20
add	x15, x13, #0x30
mla.4s	v16, v1, v0[0]
str	s16, [x13]
mov	s1, v16[1]
str	s1, [x13, #0x10]
st1.s	{ v16 }[2], [x14]
st1.s	{ v16 }[3], [x15]
mov	x13, x12
subs	x10, x10, #0x4
b.ne	0x3c <ltmp0+0x3c>
