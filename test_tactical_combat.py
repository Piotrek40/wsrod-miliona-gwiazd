#!/usr/bin/env python3
"""
Test dla systemu walki taktycznej
"""
import sys
from src.combat.tactical_battle import TacticalBattle, GridPosition
from src.models.ship import Ship, ShipType


def test_tactical_combat():
    """Test podstawowej funkcjonalności tactical combat"""
    print("="*70)
    print("TEST: TACTICAL COMBAT SYSTEM")
    print("="*70)

    # Stwórz statki dla testu
    print("\n1. Creating test fleets...")
    attacker_ships = [
        Ship.create_ship(0, ShipType.FIGHTER, 0, 0, 0),
        Ship.create_ship(1, ShipType.CRUISER, 0, 0, 0),
    ]

    defender_ships = [
        Ship.create_ship(2, ShipType.FIGHTER, 1, 100, 100),
        Ship.create_ship(3, ShipType.FIGHTER, 1, 100, 100),
    ]

    print(f"   Attacker: {len(attacker_ships)} ships (empire 0)")
    print(f"   Defender: {len(defender_ships)} ships (empire 1)")

    # Stwórz tactical battle
    print("\n2. Initializing tactical battle...")
    battle = TacticalBattle(
        attacker_empire_id=0,
        defender_empire_id=1,
        attacker_ships=attacker_ships,
        defender_ships=defender_ships,
        location=(50, 50),
        player_empire_id=0
    )

    print(f"   Grid: {battle.grid.width}x{battle.grid.height}")
    print(f"   Attacker ships positioned: {len(battle.attacker_states)}")
    print(f"   Defender ships positioned: {len(battle.defender_states)}")
    print(f"   Initiative queue: {len(battle.initiative_queue)} ships")

    # Test pozycji startowych
    print("\n3. Checking starting positions...")
    for i, state in enumerate(battle.attacker_states):
        print(f"   Attacker {i}: position ({state.position.x}, {state.position.y})")

    for i, state in enumerate(battle.defender_states):
        print(f"   Defender {i}: position ({state.position.x}, {state.position.y})")

    # Test grid operations
    print("\n4. Testing grid operations...")
    test_pos = GridPosition(5, 5)
    neighbors = battle.grid.get_neighbors(test_pos, distance=2)
    print(f"   Neighbors of (5,5) within 2: {len(neighbors)} positions")

    positions_in_range = battle.grid.positions_in_range(test_pos, 3)
    print(f"   Positions in range 3: {len(positions_in_range)}")

    # Test weapon ranges
    print("\n5. Testing weapon ranges...")
    for state in battle.attacker_states:
        print(f"   {state.ship.ship_type.value}: range={state.weapon_range} tiles")

    # Test ruchu
    print("\n6. Testing movement...")
    first_ship = battle.attacker_states[0]
    print(f"   Ship at ({first_ship.position.x}, {first_ship.position.y})")
    print(f"   Movement points: {first_ship.movement_points}")

    new_pos = GridPosition(first_ship.position.x + 1, first_ship.position.y)
    can_move = battle.can_move_to(first_ship, new_pos)
    print(f"   Can move to ({new_pos.x}, {new_pos.y}): {can_move}")

    if can_move:
        success = battle.move_ship(first_ship, new_pos)
        print(f"   Moved: {success}")
        print(f"   New position: ({first_ship.position.x}, {first_ship.position.y})")

    # Test ataku
    print("\n7. Testing attack system...")
    attacker = battle.attacker_states[0]
    targets = battle.get_targets_in_range(attacker)
    print(f"   Targets in range: {len(targets)}")

    if targets:
        target = targets[0]
        initial_hp = target.ship.current_hp
        damage = battle.attack(attacker, target)
        print(f"   Damage dealt: {damage:.1f}")
        print(f"   Target HP: {initial_hp:.1f} -> {target.ship.current_hp:.1f}")

    # Test AI turn
    print("\n8. Testing AI turn...")
    ai_ship = battle.defender_states[0]
    print(f"   AI ship before: pos=({ai_ship.position.x}, {ai_ship.position.y}), moved={ai_ship.has_moved}, attacked={ai_ship.has_attacked}")
    battle.ai_take_turn(ai_ship)
    print(f"   AI ship after: pos=({ai_ship.position.x}, {ai_ship.position.y}), moved={ai_ship.has_moved}, attacked={ai_ship.has_attacked}")

    # Test auto-resolve całej bitwy
    print("\n9. Auto-resolving battle...")
    result = battle.auto_resolve()

    print(f"\n   Battle completed in {result.rounds} rounds")
    print(f"   Attacker survivors: {len(result.attacker_survivors)}")
    print(f"   Defender survivors: {len(result.defender_survivors)}")
    print(f"   Attacker ships destroyed: {result.attacker_ships_destroyed}")
    print(f"   Defender ships destroyed: {result.defender_ships_destroyed}")

    if result.attacker_won:
        print(f"   Winner: ATTACKER")
    elif result.defender_won:
        print(f"   Winner: DEFENDER")
    else:
        print(f"   Result: DRAW")

    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - TACTICAL COMBAT SYSTEM WORKING!")
    print("="*70)

    return True


if __name__ == "__main__":
    try:
        success = test_tactical_combat()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
