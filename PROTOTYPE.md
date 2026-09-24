# v0.3 Living World test notes

The overworld output is 320x288, exactly twice the Game Boy's native width and
height. The expanded area is reconstructed from Pokemon Yellow's full map-block
buffer rather than the wrapping hardware tile map. Map objects are reconstructed
from the game's live sprite state, while the original 160x144 hardware-rendered
view remains authoritative in the center. Collision, scripts, battles, menus,
dialogue, and saves are still controlled by the original game.

Test these first:

1. In Pallet Town, hold B and walk in all four directions. Movement should be
   approximately bicycle speed and should stop immediately when B is released.
2. Walk near every edge of Pallet Town and Route 1. Watch the expanded area for
   stale, wrapped, or incorrect tiles.
3. Walk away from every NPC until that person is well outside the original
   160x144 center. They should stay visible instead of disappearing at the old
   screen edge. Check walking NPCs from all four directions.
4. Open the Start menu, talk to an NPC, enter a building, and start a battle.
   These should remain readable and should not affect saves or controls.
5. Verify biking, Cycling Road, and surfing later in the game. The runtime
   patch returns to the original bicycle routine, including Cycling Road's
   directional rule, and does not alter surfing speed.
6. Compare grass, water, roofs, characters, and menus. The vivid color treatment
   should apply only while the full overworld renderer is active; menus,
   dialogue, battles, and title screens should retain their normal colors.

Known limitation: the renderer can show distant map objects, but Pokemon Yellow
may pause their movement logic when they are far outside the original camera.
They should remain visible in the correct location and resume normal game-driven
movement when nearby.

The core recognizes Pokemon Yellow by its ROM header and checks the original
machine-code signature before applying the in-memory running patch.
