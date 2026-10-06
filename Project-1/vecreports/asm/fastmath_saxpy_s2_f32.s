; fastmath saxpy_s2 f32: largest loop body (20 instr)
ldur	s1, [x10, #-0x10]
ldur	s2, [x10, #-0x8]
ldr	s3, [x10]
ldr	s4, [x10, #0x8]
ldur	s5, [x9, #-0x10]
ldur	s6, [x9, #-0x8]
ldr	s7, [x9]
ldr	s16, [x9, #0x8]
fmadd	s1, s1, s0, s5
fmadd	s2, s2, s0, s6
fmadd	s3, s3, s0, s7
fmadd	s4, s4, s0, s16
stur	s1, [x9, #-0x10]
stur	s2, [x9, #-0x8]
str	s3, [x9]
str	s4, [x9, #0x8]
add	x9, x9, #0x20
add	x10, x10, #0x20
subs	x11, x11, #0x4
b.ne	0x28 <ltmp0+0x28>
