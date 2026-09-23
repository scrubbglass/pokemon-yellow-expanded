# Pokemon Yellow Expanded

An experimental Android ARM64 SameBoy libretro core for the US Pokemon Yellow
Game Boy Color ROM.

Prototype v0.1:

- Hold **B** while walking to run at bicycle speed.
- Expands the overworld from 160x144 to 192x176 (16 extra pixels per side).
- Keeps SameBoy's native 160x144 rendering pixel-perfect in the center.
- Centers battles, menus, and dialogue at their original size.
- Applies the running change in emulator memory; it never modifies the ROM file.

This repository contains no Pokemon ROM or copyrighted game assets. Use it with
a legally obtained US Pokemon Yellow ROM whose header title is `POKEMON YELLOW`.
