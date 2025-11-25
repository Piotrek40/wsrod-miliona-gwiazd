"""
System walki i bitew
"""
from src.combat.battle import Battle, BattleResult
from src.combat.combat_manager import CombatManager

# Combat effects require pygame - import only if available
try:
    from src.combat.combat_effects import CombatEffectsManager, LaserBeam, Explosion
    __all__ = ['Battle', 'BattleResult', 'CombatManager', 'CombatEffectsManager', 'LaserBeam', 'Explosion']
except ImportError:
    # pygame not available, skip visual effects
    CombatEffectsManager = None
    LaserBeam = None
    Explosion = None
    __all__ = ['Battle', 'BattleResult', 'CombatManager']
