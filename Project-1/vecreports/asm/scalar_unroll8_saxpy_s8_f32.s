; scalar_unroll8 saxpy_s8 f32: largest loop body (37 instr) [truncated to 24]
ldur	s1, [x12, #-0x80]
ldur	s2, [x11, #-0x80]
fmadd	s1, s0, s1, s2
stur	s1, [x11, #-0x80]
ldur	s1, [x12, #-0x60]
ldur	s2, [x11, #-0x60]
fmadd	s1, s0, s1, s2
stur	s1, [x11, #-0x60]
ldur	s1, [x12, #-0x40]
ldur	s2, [x11, #-0x40]
fmadd	s1, s0, s1, s2
stur	s1, [x11, #-0x40]
ldur	s1, [x12, #-0x20]
ldur	s2, [x11, #-0x20]
fmadd	s1, s0, s1, s2
stur	s1, [x11, #-0x20]
ldr	s1, [x12]
ldr	s2, [x11]
fmadd	s1, s0, s1, s2
str	s1, [x11]
ldr	s1, [x12, #0x20]
ldr	s2, [x11, #0x20]
fmadd	s1, s0, s1, s2
str	s1, [x11, #0x20]
