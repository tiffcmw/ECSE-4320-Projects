; auto_forcevec saxpy_s8 f32: largest loop body (12 instr)
ldr	d1, [x10, #0x20]
ldr	d2, [x10], #0x40
zip1.2s	v1, v2, v1
add	x12, x11, #0x20
ldr	d2, [x11, #0x20]
ldr	d3, [x11]
zip1.2s	v2, v3, v2
fmla.2s	v2, v1, v0[0]
str	s2, [x11], #0x40
st1.s	{ v2 }[1], [x12]
subs	x9, x9, #0x2
b.ne	0x2c <ltmp0+0x2c>
