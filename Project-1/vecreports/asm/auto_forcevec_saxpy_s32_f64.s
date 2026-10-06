; auto_forcevec saxpy_s32 f64: largest loop body (11 instr)
ldur	d1, [x9, #-0x100]
ld1.d	{ v1 }[1], [x9]
ldur	d2, [x10, #-0x100]
ld1.d	{ v2 }[1], [x10]
fmla.2d	v2, v1, v0[0]
stur	d2, [x10, #-0x100]
st1.d	{ v2 }[1], [x10]
add	x9, x9, #0x200
add	x10, x10, #0x200
subs	x11, x11, #0x2
b.ne	0x24 <ltmp0+0x24>
