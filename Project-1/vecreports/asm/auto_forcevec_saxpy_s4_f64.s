; auto_forcevec saxpy_s4 f64: largest loop body (9 instr)
ld4.2d	{ v1, v2, v3, v4 }, [x10], #64
add	x13, x12, #0x20
ld4.2d	{ v16, v17, v18, v19 }, [x11], #64
fmla.2d	v16, v1, v0[0]
str	d16, [x12]
st1.d	{ v16 }[1], [x13]
mov	x12, x11
subs	x9, x9, #0x2
b.ne	0x2c <ltmp0+0x2c>
