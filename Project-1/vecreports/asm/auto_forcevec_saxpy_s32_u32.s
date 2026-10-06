; auto_forcevec saxpy_s32 u32: largest loop body (22 instr)
sub	x13, x10, #0x80
ldur	s1, [x10, #-0x100]
ld1.s	{ v1 }[1], [x13]
ld1.s	{ v1 }[2], [x10]
add	x13, x10, #0x80
ld1.s	{ v1 }[3], [x13]
sub	x13, x11, #0x80
add	x14, x11, #0x80
ldur	s2, [x11, #-0x100]
ld1.s	{ v2 }[1], [x13]
ld1.s	{ v2 }[2], [x11]
ld1.s	{ v2 }[3], [x14]
mla.4s	v2, v1, v0[0]
stur	s2, [x11, #-0x100]
mov	s1, v2[1]
st1.s	{ v2 }[2], [x11]
stur	s1, [x11, #-0x80]
st1.s	{ v2 }[3], [x14]
add	x10, x10, #0x200
add	x11, x11, #0x200
subs	x12, x12, #0x4
b.ne	0x2c <ltmp0+0x2c>
