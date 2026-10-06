; scalar_nounroll dot f32: largest loop body (5 instr)
ldr	s1, [x1], #0x4
ldr	s2, [x2], #0x4
fmadd	s0, s1, s2, s0
subs	x0, x0, #0x1
b.ne	0x8 <ltmp0+0x8>
