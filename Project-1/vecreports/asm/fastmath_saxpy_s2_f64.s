; fastmath saxpy_s2 f64: largest loop body (20 instr)
ldur	d1, [x10, #-0x20]
ldur	d2, [x10, #-0x10]
ldr	d3, [x10]
ldr	d4, [x10, #0x10]
ldur	d5, [x9, #-0x20]
ldur	d6, [x9, #-0x10]
ldr	d7, [x9]
ldr	d16, [x9, #0x10]
fmadd	d1, d1, d0, d5
fmadd	d2, d2, d0, d6
fmadd	d3, d3, d0, d7
fmadd	d4, d4, d0, d16
stur	d1, [x9, #-0x20]
stur	d2, [x9, #-0x10]
str	d3, [x9]
str	d4, [x9, #0x10]
add	x9, x9, #0x40
add	x10, x10, #0x40
subs	x11, x11, #0x4
b.ne	0x24 <ltmp0+0x24>
