; auto_forcevec saxpy_s2 f64: largest loop body (9 instr)
ld2.2d	{ v1, v2 }, [x10], #32
add	x13, x12, #0x10
ld2.2d	{ v3, v4 }, [x11], #32
fmla.2d	v3, v1, v0[0]
str	d3, [x12]
st1.d	{ v3 }[1], [x13]
mov	x12, x11
subs	x9, x9, #0x2
b.ne	0x2c <ltmp0+0x2c>
