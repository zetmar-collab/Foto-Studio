# Foto-Studio V2.5

System zarządzania studiem fotograficznym — działa lokalnie w przeglądarce, bez potrzeby serwera zewnętrznego.

**Autor:** Marek Zettel

---

## Funkcje

- Galerie zdjęć z podglądem i organizacją
- Zarządzanie umowami i klientami
- Książka kontaktów
- Integracja z Gmailem
- Asystent AI (Claude / Anthropic)
- Kopie zapasowe z wyborem lokalizacji
- Jasny i ciemny motyw
- Obsługa Windows i macOS

---

## Wymagania

- Python 3.10 lub nowszy
- Połączenie internetowe tylko dla funkcji AI i Gmail
- Aktualna przeglądarka: Chrome, Firefox, Edge lub Safari

---

## Instalacja i uruchomienie

### Windows

```bat
start-foto-studio-windows.bat
```

### macOS

```bash
chmod +x start-foto-studio-macos.sh
./start-foto-studio-macos.sh
```

### Ręcznie

```bash
python -m venv .venv

# Windows
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py

# macOS / Linux
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Po uruchomieniu otwórz: **http://localhost:3000**

---

## Konfiguracja AI

W zakładce **Ustawienia** wklej klucz API Anthropic (Claude), lub ustaw zmienną środowiskową:

```
ANTHROPIC_API_KEY=twój_klucz
```

---

## Kopie zapasowe

Przy pierwszym uruchomieniu program poprosi o wskazanie folderu na kopie zapasowe. Zalecany jest dysk zewnętrzny lub folder synchronizowany z chmurą.

---

## Testy

```bash
# Windows
.venv\Scripts\python.exe -m unittest discover -s tests -v

# macOS / Linux
.venv/bin/python -m unittest discover -s tests -v
```

---

## Budowanie paczki

```bash
# Windows
build-windows.bat
# wynik: dist\Foto-Studio\Foto-Studio.exe

# macOS
chmod +x build-macos.sh
./build-macos.sh
# wynik: dist/Foto-Studio/Foto-Studio
```

---

## Licencja

Zobacz plik [LICENSE.txt](LICENSE.txt).
