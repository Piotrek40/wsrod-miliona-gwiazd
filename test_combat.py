"""
Test manualny systemu combat - tworzy scenariusz bitwy
"""
from src.combat.battle import Battle
from src.models.ship import Ship, ShipType

def test_combat_basic():
    """Test podstawowej bitwy"""
    print("=== TEST 1: Podstawowa bitwa 3v3 ===")

    # Stwórz atakujących (Imperium 0)
    attackers = [
        Ship.create_ship(0, ShipType.FIGHTER, 0, 100, 100),
        Ship.create_ship(1, ShipType.FIGHTER, 0, 105, 105),
        Ship.create_ship(2, ShipType.FIGHTER, 0, 110, 110),
    ]

    # Stwórz obrońców (Imperium 1)
    defenders = [
        Ship.create_ship(3, ShipType.FIGHTER, 1, 120, 120),
        Ship.create_ship(4, ShipType.FIGHTER, 1, 125, 125),
        Ship.create_ship(5, ShipType.FIGHTER, 1, 130, 130),
    ]

    print(f"Atakujący: {len(attackers)} Fighters (HP: {attackers[0].max_hp}, ATK: {attackers[0].attack}, DEF: {attackers[0].defense})")
    print(f"Obrońcy: {len(defenders)} Fighters (HP: {defenders[0].max_hp}, ATK: {defenders[0].attack}, DEF: {defenders[0].defense})")

    # Stwórz bitwę
    battle = Battle(attackers, defenders, 110, 115)

    # Wykonaj bitwę
    result = battle.execute_full_battle()

    # Wyniki
    print(f"\n⚔️ WYNIK:")
    print(f"  Atakujący wygrał: {result.attacker_won}")
    print(f"  Rundy: {result.rounds}")
    print(f"  Straty atakujących: {result.attacker_ships_destroyed}/{len(attackers)}")
    print(f"  Straty obrońców: {result.defender_ships_destroyed}/{len(defenders)}")
    print(f"  Ocalali atakujący: {len(result.attacker_survivors)}")
    print(f"  Ocalali obrońcy: {len(result.defender_survivors)}")

    # Sprawdź HP ocalałych
    if result.attacker_survivors:
        print(f"\n  HP ocalałych atakujących:")
        for ship in result.attacker_survivors:
            print(f"    {ship.name}: {ship.current_hp:.1f}/{ship.max_hp}")

    if result.defender_survivors:
        print(f"\n  HP ocalałych obrońców:")
        for ship in result.defender_survivors:
            print(f"    {ship.name}: {ship.current_hp:.1f}/{ship.max_hp}")

    assert result.rounds > 0, "Bitwa powinna mieć rundy"
    assert result.rounds <= Battle.MAX_ROUNDS, "Bitwa nie może trwać więcej niż MAX_ROUNDS"
    print("\n✅ Test passed!")


def test_combat_different_types():
    """Test bitwy z różnymi typami statków"""
    print("\n\n=== TEST 2: Różne typy statków ===")

    # Atakujący - 2 Battleships
    attackers = [
        Ship.create_ship(10, ShipType.BATTLESHIP, 0, 200, 200),
        Ship.create_ship(11, ShipType.BATTLESHIP, 0, 205, 205),
    ]

    # Obrońcy - 5 Scouts (słabi ale liczniejsi)
    defenders = [
        Ship.create_ship(20, ShipType.SCOUT, 1, 250, 250),
        Ship.create_ship(21, ShipType.SCOUT, 1, 255, 255),
        Ship.create_ship(22, ShipType.SCOUT, 1, 260, 260),
        Ship.create_ship(23, ShipType.SCOUT, 1, 265, 265),
        Ship.create_ship(24, ShipType.SCOUT, 1, 270, 270),
    ]

    print(f"Atakujący: {len(attackers)} Battleships (HP: {attackers[0].max_hp}, ATK: {attackers[0].attack}, DEF: {attackers[0].defense})")
    print(f"Obrońcy: {len(defenders)} Scouts (HP: {defenders[0].max_hp}, ATK: {defenders[0].attack}, DEF: {defenders[0].defense})")

    # Bitwa
    battle = Battle(attackers, defenders, 230, 235)
    result = battle.execute_full_battle()

    print(f"\n⚔️ WYNIK:")
    print(f"  Atakujący wygrał: {result.attacker_won}")
    print(f"  Rundy: {result.rounds}")
    print(f"  Straty: {result.attacker_ships_destroyed} Battleships vs {result.defender_ships_destroyed} Scouts")
    print(f"  Ocalali: {len(result.attacker_survivors)} atakujących, {len(result.defender_survivors)} obrońców")

    # Battleships powinny wygrać (mają dużo więcej HP i ATK)
    assert result.attacker_won, "Battleships powinny wygrać przeciwko Scouts"
    print("\n✅ Test passed!")


def test_combat_one_on_one():
    """Test pojedynku 1v1"""
    print("\n\n=== TEST 3: Pojedynek 1v1 (Cruiser vs Cruiser) ===")

    attacker = [Ship.create_ship(30, ShipType.CRUISER, 0, 300, 300)]
    defender = [Ship.create_ship(31, ShipType.CRUISER, 1, 310, 310)]

    print(f"Cruiser vs Cruiser (HP: {attacker[0].max_hp}, ATK: {attacker[0].attack}, DEF: {attacker[0].defense})")

    battle = Battle(attacker, defender, 305, 305)
    result = battle.execute_full_battle()

    print(f"\n⚔️ WYNIK:")
    print(f"  Zwycięzca: {'Atakujący' if result.attacker_won else 'Obrońca'}")
    print(f"  Rundy: {result.rounds}")

    if result.attacker_survivors:
        print(f"  HP ocalałego atakującego: {result.attacker_survivors[0].current_hp:.1f}/{result.attacker_survivors[0].max_hp}")
    if result.defender_survivors:
        print(f"  HP ocalałego obrońcy: {result.defender_survivors[0].current_hp:.1f}/{result.defender_survivors[0].max_hp}")

    # Powinien być jeden zwycięzca
    assert len(result.attacker_survivors) + len(result.defender_survivors) == 1, "Powinien być dokładnie jeden zwycięzca"
    print("\n✅ Test passed!")


if __name__ == "__main__":
    test_combat_basic()
    test_combat_different_types()
    test_combat_one_on_one()

    print("\n\n🎉 WSZYSTKIE TESTY PRZESZŁY!")
