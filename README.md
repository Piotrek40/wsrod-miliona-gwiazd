# Wśród Miliona Gwiazd 🚀

Gra strategiczna 4X w stylu Master of Orion - science fiction po polsku

## Opis

Eksploruj galaktykę, kolonizuj planety, rozwijaj technologie, buduj floty i rywalizuj z innymi cywilizacjami o dominację wśród miliona gwiazd!

### Główne mechaniki:
- 🌌 **Eksploracja** - odkrywaj 40 systemów gwiezdnych
- 🪐 **Kolonizacja** - zasiedlaj planety różnych typów
- 🔬 **Badania** - rozwijaj drzewo technologii
- 🚀 **Floty** - buduj i dowodź statkami kosmicznymi
- ⚔️ **Walki** - prowadź bitwy kosmiczne
- 🤝 **Dyplomacja** - negocjuj z AI (w przygotowaniu)

## Instalacja

### Wymagania:
- Python 3.10 lub nowszy
- pip

### Kroki instalacji:

1. Sklonuj repozytorium:
```bash
git clone <repository-url>
cd wsrod-miliona-gwiazd
```

2. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

3. Uruchom grę:
```bash
python run.py
```

lub bezpośrednio:
```bash
python src/main.py
```

## Sterowanie

- **WSAD** lub **Strzałki** - poruszanie kamerą
- **Prawy przycisk myszy** - przeciąganie mapy
- **Scroll myszy** - zoom in/out
- **+/-** - zoom z klawiatury
- **Lewy przycisk myszy** - wybór systemu gwiezdnego
- **Spacja** - zakończenie tury
- **ESC** - wyjście z gry

## Struktura projektu

```
wsrod-miliona-gwiazd/
├── src/
│   ├── main.py              # Punkt wejścia
│   ├── game.py              # Główna pętla gry
│   ├── config.py            # Konfiguracja
│   ├── models/              # Modele danych
│   │   ├── galaxy.py        # Galaktyka, systemy
│   │   ├── planet.py        # Planety
│   │   ├── empire.py        # Imperia/cywilizacje
│   │   └── ship.py          # Statki
│   ├── ui/                  # Interfejs użytkownika
│   │   ├── camera.py        # System kamery
│   │   ├── renderer.py      # Renderowanie
│   │   └── widgets.py       # Komponenty UI
│   ├── ai/                  # Sztuczna inteligencja (w przygotowaniu)
│   ├── game_logic/          # Logika gry (w przygotowaniu)
│   └── utils/               # Narzędzia (w przygotowaniu)
├── requirements.txt         # Zależności
└── run.py                   # Launcher
```

## Status projektu

**Wersja: 0.1 - Prototype (MVP)**

### ✅ Zaimplementowane:
- Generowanie galaktyki z systemami gwiezdnymi
- System kamery (ruch, zoom)
- Podstawowe UI i renderer
- Modele danych (planety, systemy, statki, imperia)
- Kolonizacja planet
- Wzrost populacji
- System tur
- Początkowe statki

### 🚧 W przygotowaniu:
- System badań technologicznych
- Produkcja statków
- Walki kosmiczne
- AI przeciwników
- Dyplomacja
- Ekonomia i handel
- Zapis/odczyt gry
- Dźwięki i muzyka

## Roadmap

Zobacz [dokumentację projektu](docs/) dla pełnego planu rozwoju.

## Licencja

[Dodaj licencję]

## Autorzy

Projekt hobbystyczny
