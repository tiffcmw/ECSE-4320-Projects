; auto_forcevec saxpy_s2 f32: largest loop body (13 instr)
ld2.4s	{ v1, v2 }, [x10], #32
add	x13, x12, #0x8
ld2.4s	{ v3, v4 }, [x11], #32
add	x14, x12, #0x10
add	x15, x12, #0x18
fmla.4s	v3, v1, v0[0]
str	s3, [x12]
st1.s	{ v3 }[1], [x13]
st1.s	{ v3 }[2], [x14]
st1.s	{ v3 }[3], [x15]
mov	x12, x11
subs	x9, x9, #0x4
b.ne	0x38 <ltmp0+0x38>
