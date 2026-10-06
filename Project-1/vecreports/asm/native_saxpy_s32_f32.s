; native saxpy_s32 f32: largest loop body (20 instr)
ldur	s1, [x10, #-0x100]
ldur	s2, [x10, #-0x80]
ldr	s3, [x10]
ldr	s4, [x10, #0x80]
ldur	s5, [x9, #-0x100]
ldur	s6, [x9, #-0x80]
ldr	s7, [x9]
ldr	s16, [x9, #0x80]
fmadd	s1, s0, s1, s5
fmadd	s2, s0, s2, s6
fmadd	s3, s0, s3, s7
fmadd	s4, s0, s4, s16
stur	s1, [x9, #-0x100]
stur	s2, [x9, #-0x80]
str	s3, [x9]
str	s4, [x9, #0x80]
add	x9, x9, #0x200
add	x10, x10, #0x200
subs	x11, x11, #0x4
b.ne	0x28 <ltmp0+0x28>
