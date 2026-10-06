; fastmath saxpy_s32 f64: largest loop body (20 instr)
ldr	d1, [x10]
ldr	d2, [x10, #0x100]
ldr	d3, [x10, #0x200]
ldr	d4, [x10, #0x300]
ldr	d5, [x9]
ldr	d6, [x9, #0x100]
ldr	d7, [x9, #0x200]
ldr	d16, [x9, #0x300]
fmadd	d1, d1, d0, d5
fmadd	d2, d2, d0, d6
fmadd	d3, d3, d0, d7
fmadd	d4, d4, d0, d16
str	d1, [x9]
str	d2, [x9, #0x100]
str	d3, [x9, #0x200]
str	d4, [x9, #0x300]
add	x10, x10, #0x400
add	x9, x9, #0x400
subs	x11, x11, #0x4
b.ne	0x24 <ltmp0+0x24>
