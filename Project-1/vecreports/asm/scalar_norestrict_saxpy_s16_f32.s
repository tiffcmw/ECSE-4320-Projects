; scalar_norestrict saxpy_s16 f32: largest loop body (6 instr)
ldr	s1, [x1], #0x40
ldr	s2, [x2]
fmadd	s1, s0, s1, s2
str	s1, [x2], #0x40
subs	x0, x0, #0x1
b.ne	0x8 <ltmp0+0x8>
