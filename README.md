# Pokemon Yellow Expanded

An experimental Android ARM64 SameBoy libretro core for the US Pokemon Yellow
Game Boy Color ROM.

Prototype v0.3.3 Natural World:

- Hold **B** while walking to run at bicycle speed.
- Expands the overworld from 160x144 to 320x288, exactly twice the native
  width and height.
- Reconstructs people and other map objects outside the original LCD camera
  from Pokemon Yellow's live sprite-state tables, so they no longer pop in at
  the old screen boundary.
- Keeps the expanded outdoor view active behind dialogue and menus instead of
  briefly collapsing the output to the original Game Boy-sized frame.
- Applies tile-aware natural colors: green grass and trees, blue water, warm
  earth and buildings, and a separate high-contrast character palette.
- Keeps the expanded renderer disabled until SameBoy's boot ROM has completely
  handed control to Pokemon Yellow, preventing randomized startup memory from
  being mistaken for a loaded map.
- Restricts the expanded renderer to outdoor tilesets and validates both axes
  of the map-block buffer before reading it.
- Constrains camera matching near Pokemon Yellow's real map pointer so repeated
  terrain cannot make the synthetic view drift into duplicated scenery.
- Keeps SameBoy's native 160x144 rendering pixel-perfect in the center.
- Centers battles and indoor maps at their original size. Dialogue and menus
  remain readable in the native center while the outdoor world stays expanded.
- Applies the running change in emulator memory; it never modifies the ROM file.

This repository contains no Pokemon ROM or copyrighted game assets. Use it with
a legally obtained US Pokemon Yellow ROM whose header title is `POKEMON YELLOW`.
