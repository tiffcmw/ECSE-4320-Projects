; native saxpy_s4 f64: largest loop body (20 instr)
ldur	d1, [x10, #-0x40]
ldur	d2, [x10, #-0x20]
ldr	d3, [x10]
ldr	d4, [x10, #0x20]
ldur	d5, [x9, #-0x40]
ldur	d6, [x9, #-0x20]
ldr	d7, [x9]
ldr	d16, [x9, #0x20]
fmadd	d1, d0, d1, d5
fmadd	d2, d0, d2, d6
fmadd	d3, d0, d3, d7
fmadd	d4, d0, d4, d16
stur	d1, [x9, #-0x40]
stur	d2, [x9, #-0x20]
str	d3, [x9]
str	d4, [x9, #0x20]
add	x9, x9, #0x80
add	x10, x10, #0x80
subs	x11, x11, #0x4
b.ne	0x24 <ltmp0+0x24>
