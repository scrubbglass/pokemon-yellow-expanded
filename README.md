# Pokemon Yellow Expanded

An experimental Android ARM64 SameBoy libretro core for the US Pokemon Yellow
Game Boy Color ROM.

Prototype v0.3.1 Boot Guard:

- Hold **B** while walking to run at bicycle speed.
- Expands the overworld from 160x144 to 320x288, exactly twice the native
  width and height.
- Reconstructs people and other map objects outside the original LCD camera
  from Pokemon Yellow's live sprite-state tables, so they no longer pop in at
  the old screen boundary.
- Applies a more saturated, higher-contrast color treatment to the expanded
  overworld.
- Keeps the expanded renderer disabled until SameBoy's boot ROM has completely
  handed control to Pokemon Yellow, preventing randomized startup memory from
  being mistaken for a loaded map.
- Keeps SameBoy's native 160x144 rendering pixel-perfect in the center.
- Centers battles, menus, and dialogue at their original size.
- Applies the running change in emulator memory; it never modifies the ROM file.

This repository contains no Pokemon ROM or copyrighted game assets. Use it with
a legally obtained US Pokemon Yellow ROM whose header title is `POKEMON YELLOW`.
