; scalar_norestrict mul f32: largest loop body (6 instr)
ldr	s0, [x1], #0x4
ldr	s1, [x2], #0x4
fmul	s0, s0, s1
str	s0, [x3], #0x4
subs	x0, x0, #0x1
b.ne	0x4 <ltmp0+0x4>
