# v0.3.3 Natural World test notes

The overworld output is 320x288, exactly twice the Game Boy's native width and
height. The expanded area is reconstructed from Pokemon Yellow's full map-block
buffer rather than the wrapping hardware tile map. Map objects are reconstructed
from the game's live sprite state, while the original 160x144 hardware-rendered
view remains authoritative in the center. Collision, scripts, battles, menus,
dialogue, and saves are still controlled by the original game.

v0.3.1 adds an explicit boot-completion guard. Version 0.3 could occasionally
mistake randomized CGB startup memory for valid overworld state on Android,
activate the expensive full-map renderer during the SameBoy logo, and appear to
hang with a fragmented logo.

v0.3.2 keeps indoor maps at the native centered view, rejects map-buffer reads
outside the current map plus its six-block connection border, and constrains
the background alignment search around the game's real camera pointer. This is
intended to remove the repeated houses, white columns, and progressive scenery
drift seen while walking around Pallet Town in v0.3.1.

v0.3.3 keeps the expanded renderer active while outdoor dialogue or the Start
menu is open, eliminating the full-screen shrink flash caused by v0.3.2's font
guard. It also replaces the generic saturation pass with tile-aware natural
color families for vegetation, water, earth/buildings, and characters.

Test these first:

1. In Pallet Town, hold B and walk in all four directions. Movement should be
   approximately bicycle speed and should stop immediately when B is released.
2. Walk near every edge of Pallet Town and Route 1. Watch the expanded area for
   stale, wrapped, or incorrect tiles.
3. Walk away from every NPC until that person is well outside the original
   160x144 center. They should stay visible instead of disappearing at the old
   screen edge. Check walking NPCs from all four directions.
4. Open the Start menu and talk to an NPC outdoors. The expanded surroundings
   should stay in place behind the native menu or text box without collapsing
   to 160x144. Enter a building and start a battle; those should still switch
   safely to the centered native view.
5. Verify biking, Cycling Road, and surfing later in the game. The runtime
   patch returns to the original bicycle routine, including Cycling Road's
   directional rule, and does not alter surfing speed.
6. Compare grass, water, roofs, paths, characters, and text. Outdoor vegetation
   should read green, water blue, and construction/earth warmer brown. Check
   that black outlines and text remain crisp and that no UI region is tinted
   strongly enough to hurt readability.

Known limitation: the renderer can show distant map objects, but Pokemon Yellow
may pause their movement logic when they are far outside the original camera.
They should remain visible in the correct location and resume normal game-driven
movement when nearby.

The core recognizes Pokemon Yellow by its ROM header and checks the original
machine-code signature before applying the in-memory running patch.
