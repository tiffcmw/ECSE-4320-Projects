; scalar_unroll8 saxpy_s8 f64: largest loop body (37 instr) [truncated to 24]
ldur	d1, [x12, #-0x100]
ldur	d2, [x11, #-0x100]
fmadd	d1, d0, d1, d2
stur	d1, [x11, #-0x100]
ldur	d1, [x12, #-0xc0]
ldur	d2, [x11, #-0xc0]
fmadd	d1, d0, d1, d2
stur	d1, [x11, #-0xc0]
ldur	d1, [x12, #-0x80]
ldur	d2, [x11, #-0x80]
fmadd	d1, d0, d1, d2
stur	d1, [x11, #-0x80]
ldur	d1, [x12, #-0x40]
ldur	d2, [x11, #-0x40]
fmadd	d1, d0, d1, d2
stur	d1, [x11, #-0x40]
ldr	d1, [x12]
ldr	d2, [x11]
fmadd	d1, d0, d1, d2
str	d1, [x11]
ldr	d1, [x12, #0x40]
ldr	d2, [x11, #0x40]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x40]
