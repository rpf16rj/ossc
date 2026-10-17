# Agent notes — ossc fork

## Build (firmware, WSL/Linux)

Toolchain lives user-local in WSL Ubuntu at `~/opt/riscv-root` (extracted
debs: gcc-riscv64-unknown-elf, binutils-riscv64-unknown-elf,
picolibc-riscv64-unknown-elf, make, iverilog). The picolibc.specs in that root
was rewritten to absolute paths (upstream deb hardcodes /usr/lib/picolibc).

```bash
# env
export PATH=$HOME/opt/riscv-root/usr/bin:/usr/bin:/bin
# symlinks in software/sys_controller_bsp/drivers/{inc,src} must be real
# symlinks — recreate with ln -s if cloned on Windows (core.symlinks=false)
touch ../sys_controller_bsp/bsp_timestamp   # once per qsys regen
cd software/sys_controller
make PICOLIBC_DIR=$HOME/opt/riscv-root/usr/lib/picolibc/riscv64-unknown-elf \
     AR=riscv64-unknown-elf-gcc-ar RANLIB=riscv64-unknown-elf-gcc-ranlib all
```

- `AR/RANLIB` must be the gcc- wrappers: plain `ar` drops LTO symbols from
  `libhal_bsp.a` (undefined `alt_load`/`alt_main` at link).
- GCC <15 needs `<stdbool.h>` where `bool` is used (fixed in it6613 sources);
  upstream implicitly relies on C23 toolchain defaults.

## RTL lint without Quartus

- `iverilog -g2012 -B ~/opt/riscv-root/usr/lib/x86_64-linux-gnu/ivl -I rtl -t null -i <file>`
  — full elaboration works for self-contained modules (ir_rcv, lat_tester).
  Files using Altera megafunctions/Quartus-only constructs (hierarchical
  defparam, wire-init `'{...}`, procedural assign to wire) fail lint even in
  upstream — check equivalence by diffing errors vs upstream file.
- `verible-verilog-syntax` at `~/opt/verible/bin/` — full SV parser, clean on
  all modified files except pre-existing upstream patterns.
- Real bitstream build still needs Quartus Prime Lite 16.1–21.1 (Cyclone IV)
  + `git submodule update --init` (ip/ibex_qsys) + Qsys generate + qsys.patch.
