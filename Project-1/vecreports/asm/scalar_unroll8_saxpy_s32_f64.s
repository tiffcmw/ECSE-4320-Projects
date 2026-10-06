; scalar_unroll8 saxpy_s32 f64: largest loop body (37 instr) [truncated to 24]
ldr	d1, [x12]
ldr	d2, [x11]
fmadd	d1, d0, d1, d2
str	d1, [x11]
ldr	d1, [x12, #0x100]
ldr	d2, [x11, #0x100]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x100]
ldr	d1, [x12, #0x200]
ldr	d2, [x11, #0x200]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x200]
ldr	d1, [x12, #0x300]
ldr	d2, [x11, #0x300]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x300]
ldr	d1, [x12, #0x400]
ldr	d2, [x11, #0x400]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x400]
ldr	d1, [x12, #0x500]
ldr	d2, [x11, #0x500]
fmadd	d1, d0, d1, d2
str	d1, [x11, #0x500]
