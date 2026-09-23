# v0.1 Running View test notes

This is deliberately a modest first expansion: 192x176 rather than a dramatic
zoom-out. The added 16-pixel border is reconstructed from the Game Boy's live
background tile map. The original 160x144 image remains untouched in the
center, so collision, animation, menus, and battles still use the real game
output.

Test these first:

1. In Pallet Town, hold B and walk in all four directions. Movement should be
   approximately bicycle speed and should stop immediately when B is released.
2. Walk near every edge of Pallet Town and Route 1. Watch the added border for
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
