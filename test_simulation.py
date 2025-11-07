#!/usr/bin/env python3
"""
Simple Game Simulation Test
Runs the game logic for multiple turns without rendering to test stability
"""

import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Run pygame without display

import pygame
pygame.init()

from src.game import Game
from src.models.ship import ShipType

def test_game_simulation():
    """Run game simulation for multiple turns"""

    print("="*70)
    print("GAME SIMULATION TEST")
    print("="*70)

    try:
        # Initialize game
        print("\n1. Initializing game...")
        game = Game()
        game.initialize_new_game()
        print("   ✅ Game initialized successfully")

        # Check initial state
        print("\n2. Checking initial state...")
        assert len(game.empires) > 0, "No empires created"
        assert game.player_empire is not None, "No player empire"
        assert len(game.ships) > 0, "No ships created"
        assert len(game.galaxy.systems) > 0, "No star systems"
        print(f"   ✅ Empires: {len(game.empires)}")
        print(f"   ✅ Ships: {len(game.ships)}")
        print(f"   ✅ Systems: {len(game.galaxy.systems)}")

        # Simulate turns
        print("\n3. Simulating 30 turns...")
        for turn in range(1, 31):
            try:
                # Update ships (movement)
                for ship in game.ships:
                    if ship.is_alive:
                        ship.update_movement(delta_time=0.016)

                # Process turn
                game.end_turn()

                if turn % 5 == 0:
                    print(f"   Turn {turn}: {len([s for s in game.ships if s.is_alive])} ships alive")

            except Exception as e:
                print(f"   ❌ ERROR on turn {turn}: {e}")
                import traceback
                traceback.print_exc()
                raise

        print("   ✅ All 30 turns completed successfully!")

        # Check final state
        print("\n4. Checking final state...")
        alive_ships = [s for s in game.ships if s.is_alive]
        print(f"   Ships alive: {len(alive_ships)}")
        print(f"   Total battles: {len(game.last_turn_battles)}")

        # Check AI is working
        print("\n5. Checking AI activity...")
        ai_produced_ships = len([s for s in game.ships if s.owner_id != game.player_empire.id])
        print(f"   AI ships: {ai_produced_ships}")

        # Check production system
        print("\n6. Checking production queues...")
        total_in_production = 0
        for system in game.galaxy.systems:
            for planet in system.planets:
                if planet.is_colonized:
                    total_in_production += len(planet.production_queue)
        print(f"   Items in production: {total_in_production}")

        # Check research
        print("\n7. Checking research...")
        researching_empires = sum(1 for e in game.empires if e.current_research is not None)
        print(f"   Empires researching: {researching_empires}/{len(game.empires)}")

        # Check exploration
        print("\n8. Checking exploration...")
        for empire in game.empires:
            print(f"   {empire.name}: {len(empire.explored_systems)} systems explored")

        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED - GAME IS STABLE!")
        print("="*70)
        return True

    except Exception as e:
        print("\n" + "="*70)
        print(f"💥 TEST FAILED: {e}")
        print("="*70)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = test_game_simulation()
    sys.exit(0 if success else 1)
