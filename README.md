Projekt zaliczeniowy. Narzędzie do wyciągania danych z Bulbapedii, chodzenia po linkach i analizy języka.

JAK ODPALIĆ:
Standardowo, biblioteki są w `requirements.txt`.

OPIS KODU:
Główny plik to `wiki_scraper.py`.

Zaimplementowałem wszystkie opcje wskazane w poleceniu, stąd nie będę ich tutaj ponownie obszernie opisywał. Jedynie wymienię najważniejsze z nich z nazwy i krótko opiszę:

1. Pobieranie tekstu: `--summary`
Wyświetla pierwszy konkretny akapit artykułu (bez HTML-a).

python wiki_scraper.py --summary "Team Rocket"

2. Zapisywanie tabeli `--table`
Zrzuca wybraną tabelę do pliku CSV.

python wiki_scraper.py --table "Type" --number 2 --first-row-is-header

3. Liczenie słów `--count-words`
Zlicza słowa z artykułu i dopisuje je do `word-counts.json`.

python wiki_scraper.py --count-words "Pikachu"

4. Crawler `--auto-count-words`
Chodzi po linkach (do podanej głębokości) i zlicza słowa ze wszystkich odwiedzonych stron.

python wiki_scraper.py --auto-count-words "Bulbasaur" --depth 2 --wait 1

5. Analiza statystyczna `--analyze-relative-word-frequency`
Porównuje słowa zebrane w jsonie z bazą częstotliwości języka (korzystam z `wordfreq`). Rysuje wykres.

python wiki_scraper.py --analyze-relative-word-frequency --mode article --count 20 --chart wynik.png

ANALIZA
W pliku `analiza.ipynb` znajduje się badanie skuteczności wykrywania języka. Porównałem tam angielski, polski i francuski.
Wnioski są w notatniku.

TESTY
Żeby mieć pewność, że nic nie wybuchnie:

1. unit_tests.py `pytest` (testują pojedyncze metody bez internetu).
2. integration_test.py `python wiki_scraper_integration_test.py` (sprawdza działanie `--summary` na lokalnym pliku `Team_Rocket.html`).
