; auto_forcevec saxpy_s8 f64: largest loop body (12 instr)
ldr	q1, [x10, #0x40]
ldr	q2, [x10], #0x80
zip1.2d	v1, v2, v1
add	x12, x11, #0x40
ldr	q2, [x11, #0x40]
ldr	q3, [x11]
zip1.2d	v2, v3, v2
fmla.2d	v2, v1, v0[0]
str	d2, [x11], #0x80
st1.d	{ v2 }[1], [x12]
subs	x9, x9, #0x2
b.ne	0x28 <ltmp0+0x28>
