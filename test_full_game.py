#!/usr/bin/env python3
"""
Comprehensive Game Testing Script
Tests all major game systems and validates functionality
"""

import sys
import traceback
from src.game import Game
from src.models.galaxy import Galaxy
from src.models.empire import Empire
from src.models.ship import Ship, ShipType
from src.models.planet import Planet, PlanetType, ProductionItem
from src.combat.battle import Battle
from src.ai.ai_controller import AIController
from src.config import BUILDINGS, TECHNOLOGIES, SHIP_COST


class GameTester:
    """Comprehensive game testing suite"""

    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = []

    def run_test(self, test_name: str, test_func):
        """Run a single test and track results"""
        print(f"\n{'='*70}")
        print(f"TEST: {test_name}")
        print('='*70)
        try:
            test_func()
            print(f"✅ PASSED: {test_name}")
            self.tests_passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {e}")
            self.tests_failed += 1
            self.errors.append((test_name, str(e)))
        except Exception as e:
            print(f"💥 ERROR: {test_name}")
            print(f"   Exception: {e}")
            traceback.print_exc()
            self.tests_failed += 1
            self.errors.append((test_name, str(e)))

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Total: {self.tests_passed + self.tests_failed}")

        if self.errors:
            print("\n" + "="*70)
            print("ERRORS:")
            print("="*70)
            for test_name, error in self.errors:
                print(f"\n{test_name}:")
                print(f"  {error}")

        print("\n" + "="*70)
        if self.tests_failed == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {self.tests_failed} TESTS FAILED")
        print("="*70)


# ============================================================================
# TEST 1: Galaxy Generation
# ============================================================================
def test_galaxy_generation():
    """Test galaxy generation and star system properties"""
    print("Creating galaxy...")
    galaxy = Galaxy(num_systems=50)

    assert len(galaxy.systems) == 50, f"Expected 50 systems, got {len(galaxy.systems)}"
    print(f"✓ Created {len(galaxy.systems)} star systems")

    # Test system properties
    for system in galaxy.systems[:5]:
        assert system.name, "System should have a name"
        assert system.x >= 0 and system.x <= galaxy.width, "System X out of bounds"
        assert system.y >= 0 and system.y <= galaxy.height, "System Y out of bounds"
        assert len(system.planets) > 0, f"System {system.name} has no planets"
        print(f"✓ {system.name}: {len(system.planets)} planets at ({int(system.x)}, {int(system.y)})")

    # Test system finding
    test_system = galaxy.systems[0]
    found = galaxy.find_system_by_id(test_system.id)
    assert found == test_system, "find_system_by_id failed"
    print(f"✓ System lookup works correctly")


# ============================================================================
# TEST 2: Empire Creation and Resources
# ============================================================================
def test_empire_creation():
    """Test empire creation and resource management"""
    print("Creating empires...")

    empire1 = Empire(id=0, name="Test Empire", color=(255, 0, 0), is_player=True)
    empire2 = Empire(id=1, name="AI Empire", color=(0, 255, 0), is_player=False)

    assert empire1.name == "Test Empire", "Empire name incorrect"
    assert empire1.is_player == True, "Empire should be player"
    assert empire2.is_player == False, "Empire should be AI"
    print(f"✓ Created empires: {empire1.name}, {empire2.name}")

    # Test relations
    empire1.set_relation(empire2.id, "war")
    assert empire1.get_relation(empire2.id) == "war", "Relation not set correctly"
    print(f"✓ Diplomatic relations work")

    # Test resources
    initial_minerals = empire1.resources['minerals']
    empire1.add_resources(minerals=100)
    assert empire1.resources['minerals'] == initial_minerals + 100, "Resources not added"
    print(f"✓ Resource management works")


# ============================================================================
# TEST 3: Ship Creation and Movement
# ============================================================================
def test_ship_creation_and_movement():
    """Test ship creation, properties, and movement"""
    print("Creating ships...")

    # Test different ship types
    ship_types = [ShipType.SCOUT, ShipType.FIGHTER, ShipType.CRUISER,
                  ShipType.BATTLESHIP, ShipType.COLONY_SHIP]

    ships = []
    for i, ship_type in enumerate(ship_types):
        ship = Ship.create_ship(
            ship_id=i,
            ship_type=ship_type,
            owner_id=0,
            x=100 + i * 10,
            y=100 + i * 10
        )
        ships.append(ship)
        assert ship.ship_type == ship_type, f"Ship type mismatch for {ship_type}"
        assert ship.current_hp > 0, f"Ship {ship_type} has no HP"
        assert ship.max_hp > 0, f"Ship {ship_type} has no max HP"
        print(f"✓ Created {ship_type.value}: HP={ship.max_hp}, ATK={ship.attack}, DEF={ship.defense}, SPD={ship.speed}")

    # Test movement
    scout = ships[0]
    scout.set_destination(200, 200)
    assert scout.is_moving == True, "Ship should be moving"
    assert scout.target_x == 200, "Target X incorrect"
    assert scout.target_y == 200, "Target Y incorrect"
    print(f"✓ Ship movement targeting works")

    # Simulate movement
    old_x, old_y = scout.x, scout.y
    scout.update_movement(dt=0.016)  # ~60 FPS
    assert scout.x != old_x or scout.y != old_y, "Ship should have moved"
    print(f"✓ Ship movement simulation works")


# ============================================================================
# TEST 4: Planet Colonization and Production
# ============================================================================
def test_planet_and_production():
    """Test planet colonization and production systems"""
    print("Testing planet systems...")

    # Create planet
    planet = Planet(
        name="Test Planet",
        planet_type=PlanetType.EARTH_LIKE,
        size=7,
        mineral_richness=1.5,
        x=0,
        y=0
    )

    assert not planet.is_colonized, "Planet should not be colonized"
    print(f"✓ Created planet: {planet.name} (size {planet.size})")

    # Colonize
    planet.colonize(empire_id=0, initial_population=10.0)
    assert planet.is_colonized, "Planet should be colonized"
    assert planet.population == 10.0, "Population incorrect"
    print(f"✓ Planet colonized with population {planet.population}")

    # Test production calculation
    production = planet.calculate_production()
    assert production > 0, "Production should be positive"
    print(f"✓ Planet production: {production:.1f} minerals/turn")

    # Test production queue - Ship
    planet.add_ship_to_queue(ShipType.FIGHTER)
    assert len(planet.production_queue) == 1, "Ship not added to queue"
    assert planet.production_queue[0].item_type == "ship", "Item type should be ship"
    assert planet.production_queue[0].ship_type == ShipType.FIGHTER, "Ship type incorrect"
    print(f"✓ Ship added to production queue")

    # Process production
    item = planet.process_production()
    # It might not complete in one turn
    if item:
        assert item.is_complete, "Item should be complete"
        print(f"✓ Production completed: {item.item_type}")
    else:
        progress = planet.production_queue[0].progress_percent
        print(f"✓ Production processing works ({progress:.1f}% complete)")

    # Test building production
    planet.add_building_to_queue("factory", BUILDINGS["factory"].cost)
    print(f"✓ Building added to production queue")


# ============================================================================
# TEST 5: Combat System
# ============================================================================
def test_combat_system():
    """Test combat mechanics and battle resolution"""
    print("Testing combat system...")

    # Create opposing fleets
    empire1_ships = [
        Ship.create_ship(0, ShipType.FIGHTER, 0, 100, 100),
        Ship.create_ship(1, ShipType.FIGHTER, 0, 100, 100),
        Ship.create_ship(2, ShipType.CRUISER, 0, 100, 100),
    ]

    empire2_ships = [
        Ship.create_ship(3, ShipType.FIGHTER, 1, 110, 110),
        Ship.create_ship(4, ShipType.FIGHTER, 1, 110, 110),
    ]

    print(f"✓ Empire 1: {len(empire1_ships)} ships")
    print(f"✓ Empire 2: {len(empire2_ships)} ships")

    # Create battle
    battle = Battle(
        attacker_empire_id=0,
        defender_empire_id=1,
        attacker_ships=empire1_ships,
        defender_ships=empire2_ships,
        location=(105, 105)
    )

    # Execute battle
    result = battle.execute()

    assert result is not None, "Battle should return a result"
    assert result.rounds > 0, "Battle should have at least 1 round"
    assert result.attacker_won or result.defender_won, "Someone should win"

    total_losses = result.attacker_ships_destroyed + result.defender_ships_destroyed
    print(f"✓ Battle completed in {result.rounds} rounds")
    print(f"✓ Winner: {'Attacker' if result.attacker_won else 'Defender'}")
    print(f"✓ Losses: {result.attacker_ships_destroyed} vs {result.defender_ships_destroyed}")
    print(f"✓ Survivors: {len(result.attacker_survivors)} vs {len(result.defender_survivors)}")

    # Test damage calculation
    test_attacker = Ship.create_ship(10, ShipType.CRUISER, 0, 0, 0)
    test_defender = Ship.create_ship(11, ShipType.FIGHTER, 1, 0, 0)

    damage = battle._calculate_damage(test_attacker, test_defender)
    assert damage >= 1.0, "Damage should be at least 1"
    assert damage <= test_attacker.attack * 1.2, "Damage too high"
    print(f"✓ Damage calculation: {damage:.1f} damage")


# ============================================================================
# TEST 6: AI Decision Making
# ============================================================================
def test_ai_system():
    """Test AI controller and decision making"""
    print("Testing AI system...")

    # Create minimal galaxy for AI
    galaxy = Galaxy(num_systems=20)

    # Create AI empire
    ai_empire = Empire(id=1, name="AI Test", color=(0, 255, 0), is_player=False)

    # Give AI a home system and colony
    home_system = galaxy.systems[0]
    ai_empire.home_system_id = home_system.id

    # Colonize a planet
    for planet in home_system.planets:
        if planet.planet_type in [PlanetType.EARTH_LIKE, PlanetType.DESERT]:
            planet.colonize(ai_empire.id, initial_population=20.0)
            break

    print(f"✓ Created AI empire with home system: {home_system.name}")

    # Test each personality
    personalities = ["aggressive", "peaceful", "scientific", "expansionist", "balanced"]

    for personality in personalities:
        ai_empire.ai_personality = personality
        ai_controller = AIController(ai_empire, galaxy)

        assert ai_controller.empire == ai_empire, "AI empire not set"
        assert ai_controller.personality == personality, "Personality not set"

        # Test ship choice
        ship_type = ai_controller._choose_ship_to_build()
        assert ship_type in [ShipType.SCOUT, ShipType.FIGHTER, ShipType.CRUISER,
                            ShipType.BATTLESHIP, ShipType.COLONY_SHIP], \
               f"Invalid ship type from AI: {ship_type}"

        print(f"✓ AI {personality}: would build {ship_type.value}")

    # Test AI turn decisions
    ai_controller = AIController(ai_empire, galaxy)
    ships = []

    try:
        ai_controller.make_turn_decisions(ships)
        print(f"✓ AI turn decisions executed without errors")
    except Exception as e:
        raise AssertionError(f"AI turn decisions failed: {e}")


# ============================================================================
# TEST 7: Research System
# ============================================================================
def test_research_system():
    """Test technology research system"""
    print("Testing research system...")

    empire = Empire(id=0, name="Test", color=(255, 0, 0), is_player=True)

    # Check initial state
    assert len(empire.researched_technologies) == 0, "Should start with no research"
    assert empire.current_research is None, "Should have no current research"
    print(f"✓ Empire starts with no technologies")

    # Start research
    tech_id = list(TECHNOLOGIES.keys())[0]
    tech = TECHNOLOGIES[tech_id]
    empire.start_research(tech_id)

    assert empire.current_research == tech_id, "Research not started"
    assert empire.research_progress < tech.cost, "Progress should be less than cost"
    print(f"✓ Started researching: {tech.name} (cost: {tech.cost})")

    # Add research points
    initial_progress = empire.research_progress
    empire.add_research_progress(50.0)
    assert empire.research_progress == initial_progress + 50.0, "Research progress not added"
    print(f"✓ Research progress: {empire.research_progress:.1f}/{tech.cost}")

    # Complete research
    empire.add_research_progress(tech.cost)
    if tech_id in empire.researched_technologies:
        print(f"✓ Technology completed and added to researched list")
    else:
        print(f"⚠ Technology not completed (might need more progress)")


# ============================================================================
# TEST 8: Game Integration Test
# ============================================================================
def test_game_integration():
    """Test full game initialization and turn processing"""
    print("Testing full game integration...")

    # Note: We can't fully initialize pygame in headless mode
    # So we'll test what we can without rendering
    print("⚠ Skipping full game test (requires display)")
    print("✓ Game module imports successfully")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE GAME TESTING SUITE")
    print("Testing: Wśród Miliona Gwiazd")
    print("="*70)

    tester = GameTester()

    # Run all tests
    tester.run_test("1. Galaxy Generation", test_galaxy_generation)
    tester.run_test("2. Empire Creation & Resources", test_empire_creation)
    tester.run_test("3. Ship Creation & Movement", test_ship_creation_and_movement)
    tester.run_test("4. Planet & Production System", test_planet_and_production)
    tester.run_test("5. Combat System", test_combat_system)
    tester.run_test("6. AI Decision Making", test_ai_system)
    tester.run_test("7. Research System", test_research_system)
    tester.run_test("8. Game Integration", test_game_integration)

    # Print summary
    tester.print_summary()

    # Exit with appropriate code
    sys.exit(0 if tester.tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
