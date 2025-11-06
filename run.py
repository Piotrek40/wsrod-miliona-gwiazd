#!/usr/bin/env python3
"""
Uruchom grę "Wśród Miliona Gwiazd"
"""
import sys
import os

# Dodaj katalog src do ścieżki
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
