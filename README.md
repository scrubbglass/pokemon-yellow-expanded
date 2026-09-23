# Pokemon Yellow Expanded

An experimental Android ARM64 SameBoy libretro core for the US Pokemon Yellow
Game Boy Color ROM.

Prototype v0.2:

- Hold **B** while walking to run at bicycle speed.
- Expands the overworld from 160x144 to 256x224 (48 extra pixels on each side
  and 40 extra pixels above and below).
- Reconstructs the expanded area from Pokemon Yellow's full map-block buffer
  instead of stale off-screen VRAM tiles.
- Keeps SameBoy's native 160x144 rendering pixel-perfect in the center.
- Centers battles, menus, and dialogue at their original size.
- Applies the running change in emulator memory; it never modifies the ROM file.

This repository contains no Pokemon ROM or copyrighted game assets. Use it with
a legally obtained US Pokemon Yellow ROM whose header title is `POKEMON YELLOW`.
