; scalar_nounroll stencil f32: largest loop body (8 instr)
ldur	s3, [x8, #-0x8]
fmul	s0, s0, s1
fmadd	s3, s3, s2, s0
ldr	s0, [x8], #0x4
fmadd	s3, s0, s2, s3
str	s3, [x9], #0x4
subs	x10, x10, #0x1
b.ne	0x20 <ltmp0+0x20>
