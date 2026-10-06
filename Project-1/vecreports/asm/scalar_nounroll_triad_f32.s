; scalar_nounroll triad f32: largest loop body (6 instr)
ldr	s1, [x1], #0x4
ldr	s2, [x2], #0x4
fmadd	s1, s0, s2, s1
str	s1, [x3], #0x4
subs	x0, x0, #0x1
b.ne	0x8 <ltmp0+0x8>
