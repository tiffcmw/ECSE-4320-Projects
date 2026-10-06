; scalar_norestrict gather f32: largest loop body (7 instr)
ldr	w8, [x3], #0x4
ldr	s1, [x1, x8, lsl #2]
ldr	s2, [x2]
fmadd	s1, s0, s1, s2
str	s1, [x2], #0x4
subs	x0, x0, #0x1
b.ne	0x8 <ltmp0+0x8>
