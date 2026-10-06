; auto_forcevec saxpy_s16 f32: largest loop body (11 instr)
ldur	s1, [x9, #-0x40]
ld1.s	{ v1 }[1], [x9]
ldur	s2, [x10, #-0x40]
ld1.s	{ v2 }[1], [x10]
fmla.2s	v2, v1, v0[0]
stur	s2, [x10, #-0x40]
st1.s	{ v2 }[1], [x10]
add	x9, x9, #0x80
add	x10, x10, #0x80
subs	x11, x11, #0x2
b.ne	0x28 <ltmp0+0x28>
