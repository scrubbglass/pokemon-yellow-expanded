# v0.2 Full Map View test notes

This build expands the overworld to 256x224. The larger area is reconstructed
from Pokemon Yellow's complete WRAM map-block buffer and current tileset
definitions instead of assuming unused portions of the Game Boy VRAM tilemap
contain valid nearby scenery. The original 160x144 image remains untouched in
the center, so collision, animation, menus, and battles still use the real game
output.

Test these first:

1. In Pallet Town, hold B and walk in all four directions. Movement should be
   approximately bicycle speed and should stop immediately when B is released.
2. Walk near every edge of Pallet Town and Route 1. Watch the expanded area for
   stale, wrapped, or incorrect tiles.
3. Walk past NPCs and Pikachu near the edge of the old screen. Note whether they
   appear naturally in the added border or pop into existence at the old edge.
4. Open the Start menu, talk to an NPC, enter a building, and start a battle.
   These should remain readable and should not affect saves or controls.
5. Verify biking, Cycling Road, and surfing later in the game. The runtime
   patch returns to the original bicycle routine, including Cycling Road's
   directional rule, and does not alter surfing speed.

The core recognizes Pokemon Yellow by its ROM header and checks the original
machine-code signature before applying the in-memory running patch.
