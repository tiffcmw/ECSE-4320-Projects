; auto saxpy_s16 f32: largest loop body (20 instr)
ldur	s1, [x10, #-0x80]
ldur	s2, [x10, #-0x40]
ldr	s3, [x10]
ldr	s4, [x10, #0x40]
ldur	s5, [x9, #-0x80]
ldur	s6, [x9, #-0x40]
ldr	s7, [x9]
ldr	s16, [x9, #0x40]
fmadd	s1, s0, s1, s5
fmadd	s2, s0, s2, s6
fmadd	s3, s0, s3, s7
fmadd	s4, s0, s4, s16
stur	s1, [x9, #-0x80]
stur	s2, [x9, #-0x40]
str	s3, [x9]
str	s4, [x9, #0x40]
add	x9, x9, #0x100
add	x10, x10, #0x100
subs	x11, x11, #0x4
b.ne	0x28 <ltmp0+0x28>
