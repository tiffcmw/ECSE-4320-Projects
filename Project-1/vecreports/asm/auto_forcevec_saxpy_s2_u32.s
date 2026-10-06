; auto_forcevec saxpy_s2 u32: largest loop body (13 instr)
ld2.4s	{ v1, v2 }, [x11], #32
ld2.4s	{ v3, v4 }, [x12], #32
add	x14, x13, #0x10
add	x15, x13, #0x18
mla.4s	v3, v1, v0[0]
str	s3, [x13]
mov	s1, v3[1]
str	s1, [x13, #0x8]
st1.s	{ v3 }[2], [x14]
st1.s	{ v3 }[3], [x15]
mov	x13, x12
subs	x10, x10, #0x4
b.ne	0x3c <ltmp0+0x3c>
