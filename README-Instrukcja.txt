==================================================
  Foto-Studio V2.5 - System Zarządzania Studiem
  Autor: Marek Zettel
==================================================

INSTALACJA I URUCHOMIENIE
-------------------------
Windows:
  dwuklik na start-foto-studio-windows.bat

macOS:
  chmod +x start-foto-studio-macos.sh
  ./start-foto-studio-macos.sh

Ręcznie:
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt   (Windows)
  .venv/bin/python -m pip install -r requirements.txt           (macOS)
  python app.py

Po uruchomieniu otwórz:
  http://localhost:3000

FUNKCJE
-------
- działa lokalnie w Pythonie przez Flask,
- obsługuje Windows i macOS,
- ma jasny i ciemny motyw w Ustawieniach,
- pokazuje nazwę Foto-Studio, wersję 2.5 i autora Marek Zettel,
- zawiera kopie zapasowe, galerie zdjęć, umowy, kontakty, Gmail i asystenta AI.

KONFIGURACJA AI
---------------
W Ustawieniach wklej klucz API Anthropic (Claude).
Możesz też ustawić zmienną środowiskową ANTHROPIC_API_KEY.

KOPIA ZAPASOWA
--------------
Przy pierwszym uruchomieniu program poprosi o wskazanie folderu na kopie zapasowe.
Zalecany jest dysk zewnętrzny lub folder synchronizowany.

WYMAGANIA
---------
- Python 3.10 lub nowszy,
- połączenie internetowe tylko dla funkcji AI i Gmail,
- aktualna przeglądarka: Chrome, Firefox, Edge lub Safari.

TESTY
-----
Windows:
  .venv\Scripts\python.exe -m unittest discover -s tests -v

macOS:
  .venv/bin/python -m unittest discover -s tests -v

BUDOWANIE PACZKI
----------------
Windows:
  build-windows.bat
  wynik: dist\Foto-Studio\Foto-Studio.exe

macOS:
  chmod +x build-macos.sh
  ./build-macos.sh
  wynik: dist/Foto-Studio/Foto-Studio

==================================================
