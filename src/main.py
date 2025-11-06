"""
Wśród Miliona Gwiazd
Tekstowa gra strategiczna science fiction po polsku

Punkt wejścia do gry
"""
import sys
from src.game import Game


def main():
    """Główna funkcja programu"""
    print("=" * 60)
    print("          WŚRÓD MILIONA GWIAZD")
    print("    Gra strategiczna 4X - Science Fiction")
    print("=" * 60)
    print()

    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\n\nGra przerwana przez użytkownika.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nBłąd krytyczny: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\nDziękujemy za grę!")


if __name__ == "__main__":
    main()
