; scalar_norestrict stencil f32: largest loop body (8 instr)
ldp	s2, s3, [x8, #-0x4]
fmul	s3, s3, s0
fmadd	s2, s2, s1, s3
ldr	s3, [x8, #0x4]!
fmadd	s2, s3, s1, s2
str	s2, [x9], #0x4
subs	x10, x10, #0x1
b.ne	0x1c <ltmp0+0x1c>
