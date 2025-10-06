# Finance and Project Management Toolkit

This repository provides a Python-based toolkit for managing company finances, creating offers, planning project budgets and issuing invoices zgodnie z polskimi przepisami. Narzędzie jest oparte na kilku modułach, które można wykorzystać w aplikacji webowej, narzędziu CLI lub we własnych skryptach automatyzujących.

## Wymagania

* Python 3.10+
* `matplotlib` do generowania wykresów (instalacja: `pip install matplotlib`).

## Struktura modułów

### Moduł kosztów firmy (`finance_app.company_costs`)

* **Pracownicy na umowę o pracę** – przechowuje dane brutto/netto oraz składowe wynagrodzeń.
* **Koszty utrzymania biura** – rejestruje faktury za czynsz, media, artykuły biurowe itd.
* **Koszty dodatkowe** – np. ubezpieczenia firmy.
* **Koszty leasingów** – obsługuje podział kosztów na część 50% i 100% kosztów uzyskania przychodu.
* **Wynagrodzenia zarządu** – wraz z wyliczeniem podatku dochodowego według polskiej skali podatkowej.
* **Funkcja roboczogodziny** – oblicza koszt roboczogodziny przy założeniu np. 80 roboczogodzin tygodniowo na pracownika.

### Moduł ofertowania (`finance_app.offer_module`)

* Oblicza cenę roboczogodziny na podstawie kosztów firmy.
* Wycenia projekty uwzględniając liczbę roboczogodzin i koszt materiałów.
* Dodaje marżę do materiałów oraz do roboczogodziny.
* Wspiera dni płatne 200% stawki (double time).
* Dodaje koszty dojazdu, hotelu oraz diety.
* Wizualizuje strukturę oferty na wykresie kołowym (marża, koszty, zysk).

### Moduł projektowy (`finance_app.project_module`)

* **Budżet pracowniczy** – przydziela pracowników i kontroluje planowany koszt.
* **Budżet socjalny** – planuje koszty noclegów, diet i kontenera socjalnego.
* **Budżet materiałowy** – przechowuje i sumuje koszty materiałów.
* **Protokoły odbioru** – obsługuje protokoły odbioru prac częściowych i całościowych.

### Moduł fakturowania (`finance_app.invoicing`)

* Generuje faktury na podstawie protokołów odbioru.
* Zawiera dane wystawcy, nabywcy, numer NIP, rachunek bankowy, terminy płatności.
* Sumuje kwoty netto, VAT i brutto.

## Interfejs webowy

Dla wygodniejszej pracy przygotowany został prosty interfejs webowy w oparciu o Flask. Pozwala on zarządzać wszystkimi modułami: kosztami firmy, ofertowaniem, budżetem projektu oraz fakturowaniem.

### Szybki start

1. Sklonuj repozytorium lub pobierz przygotowane archiwum (`dist/finance_app_bundle.zip`).
2. Uruchom skrypt bootstrapujący, aby zainstalować zależności w wirtualnym środowisku:

   **Linux / macOS**

   ```bash
   bash scripts/bootstrap.sh
   source .venv/bin/activate
   ```

   **Windows (PowerShell)**

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
   .\.venv\Scripts\activate
   ```

3. Uruchom interfejs webowy:

   ```bash
   flask --app app run
   ```

### Uruchomienie

```bash
pip install -r requirements.txt
flask --app app run
```

Po uruchomieniu aplikacja będzie dostępna pod adresem [http://localhost:5000](http://localhost:5000). Wszystkie dane przechowywane są w pamięci, dlatego po restarcie serwera zaczynasz z pustym zestawem.

### Jak pobrać i uruchomić program w Windows

1. **Zainstaluj Pythona 3.10+** z [python.org](https://www.python.org/downloads/windows/) i podczas instalacji zaznacz opcję *Add Python to PATH*.
2. **Pobierz kod źródłowy**:
   * jeśli masz zainstalowanego gita – uruchom w PowerShellu polecenie `git clone <adres_repozytorium>` i przejdź do katalogu projektu (`cd hello-world`),
   * w przeciwnym razie pobierz archiwum `.zip` wygenerowane poleceniem `python scripts/prepare_bundle.py` (dostępne w katalogu `dist/finance_app_bundle.zip`) i rozpakuj je w wybranym katalogu.
3. **Otwórz PowerShell w katalogu projektu** (Shift + PPM → „Otwórz okno PowerShell tutaj” lub poleceniem `cd`).
4. **Uruchom skrypt bootstrapujący** tworzący wirtualne środowisko i instalujący wymagane pakiety:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
   ```

   Skrypt utworzy katalog `.venv` i zainstaluje pakiety z `requirements.txt`.
5. **Aktywuj wirtualne środowisko**:

   ```powershell
   .\.venv\Scripts\activate
   ```

6. **Uruchom aplikację webową**:

   ```powershell
   flask --app app run
   ```

   Po chwili aplikacja będzie dostępna pod adresem `http://localhost:5000`. Zatrzymasz ją skrótem `Ctrl+C` w tym samym oknie.
7. (Opcjonalnie) **Uruchom przykładowy scenariusz CLI**:

   ```powershell
   python example_usage.py
   ```

   Skrypt wygeneruje przykładowy wykres w katalogu `images/`.

### Przygotowanie paczki do pobrania

Aby przygotować archiwum `.zip` z kompletem plików (kod źródłowy, szablony, statyczne zasoby oraz skrypty uruchomieniowe), użyj:

```bash
python scripts/prepare_bundle.py
```

Archiwum trafi do katalogu `dist/`. Można je udostępnić użytkownikom, którzy po rozpakowaniu wykonują kroki z sekcji „Szybki start”.

## Przykład użycia modułów w Pythonie

Plik `example_usage.py` nadal pokazuje kompletny przepływ od konfiguracji kosztów firmy, poprzez przygotowanie oferty, plan projektu aż do wystawienia faktury.

```bash
python example_usage.py
```

Skrypt wypisze kluczowe wartości i zapisze wykres struktury oferty w katalogu `images/`.

## Dalsze kroki

Moduły są przygotowane do dalszej rozbudowy – można je zintegrować z bazą danych, rozbudowanym interfejsem webowym lub narzędziami raportującymi.
