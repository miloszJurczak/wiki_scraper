import argparse
import json
import time
from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup
from wordfreq import word_frequency, top_n_list

# Stałe
BULBAPEDIA_URL = 'https://bulbapedia.bulbagarden.net/wiki/'
WORD_COUNTS_FILE = './word-counts.json'


class Scraper:
    def __init__(self, base_url: str, phrase: str, use_local_file: bool = False):
        self.base_url = base_url
        self.phrase = phrase
        self.use_local_file = use_local_file

    def check_if_exists(self, soup: BeautifulSoup) -> bool:
        """
        Sprawdza czy strona istnieje.
        Jeśli znajdzie komunikat o braku artykułu, zwraca False.
        """
        location_not_found = soup.find('div', class_='noarticletext mw-content-ltr')
        if location_not_found:
            paragraph = location_not_found.find('p')
            if paragraph:
                error_message = paragraph.get_text(separator=' ', strip=True)
                print(f'Strona nie istnieje. Tekst błędu strony:\n{error_message}')
                return False
        return True

    def get_soup(self) -> Optional[BeautifulSoup]:
        argument = self.phrase.replace(' ', '_')

        # Obsługa pliku lokalnego
        if self.use_local_file:
            try:
                with open(f"{argument}.html", 'r', encoding='utf-8') as f:
                    return BeautifulSoup(f, 'html.parser')
            except FileNotFoundError:
                print(f"Nie znaleziono pliku lokalnego: {argument}.html")
                return None

        # Obsługa sieci
        try:
            response = requests.get(f'{self.base_url}{argument}', timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Błąd połączenia: {e}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        if self.check_if_exists(soup):
            return soup
        else:
            return None


class SingleArticleProcessing:
    """
    Klasa odpowiedzialna za procesowanie i operacje na pojedynczym artykule.
    """
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup

    def process_summary(self) -> Optional[str]:
        """Wyświetla pierwszy paragraf strony."""
        soup = self.soup
        locations_first_paragraph = soup.find('div', class_="mw-content-ltr mw-parser-output")
        final_first_paragraph = None

        if locations_first_paragraph:
            paragraph = locations_first_paragraph.find('p')
            if paragraph:
                final_first_paragraph = ' '.join(paragraph.text.split())
                print(final_first_paragraph)
            else:
                print("Nie znaleziono paragrafu!")
        else:
            print("Nie znaleziono treści!")
        
        return final_first_paragraph

    def process_table(self, argument_name: str, number_of_table: int, header: bool) -> None:
        """Wyświetla i zapisuje wskazaną tabelę."""
        soup = self.soup
        all_tables = soup.find_all('table')
        
        if number_of_table > len(all_tables) or number_of_table < 1:
            print("Nie znaleziono tabeli o podanym numerze")
            return

        index = number_of_table - 1
        table = all_tables[index]
        
        table_data = []
        rows = table.find_all('tr')
        
        for row in rows:
            row_data = []
            # recursive=False gwarantuje że nie pobierzemy śmieci z zagnieżdżonych tabel
            cells = row.find_all(['td', 'th'], recursive=False)

            for cell in cells:
                clean_cell_text = cell.get_text(separator=' ', strip=True)
                row_data.append(clean_cell_text)
            
            if row_data:
                table_data.append(row_data)

        if not table_data:
            print("Tabela jest pusta.")
            return

        df = pd.DataFrame(table_data)
        write_header = False

        if header:
            num_columns_data = df.shape[1]
            if len(table_data) > 0:
                num_columns_header = len(table_data[0])

                if num_columns_header == num_columns_data:
                    new_header = df.iloc[0]
                    df = df[1:]
                    df.columns = new_header
                    write_header = True
                else:
                    print(f"Nagłówek ma inną liczbę kolumn ({num_columns_header}) "
                          f"niż dane ({num_columns_data}). Pomijam nagłówek.")

        filename = f"{argument_name.replace(' ', '_')}.csv"
        df.to_csv(filename, index=False, header=write_header, encoding='utf-8-sig')
        
        print(f"Zapisano do: {filename}")
        print(df)

    def raw_text_to_list(self, raw_text: str) -> List[str]:
        """Czyści tekst i zamienia go na listę słów."""
        text = raw_text.lower()
        text = ' '.join(text.split())
        text = ''.join(c for c in text if c.isalpha() or c.isspace())
        return text.split()

    def update_word_counts(self) -> None:
        """Liczy słowa i aktualizuje plik JSON."""
        soup = self.soup
        if soup is None:
            return

        content_div = soup.find('div', class_='mw-parser-output')

        if content_div:
            paragraphs = content_div.find_all('p')
            content_text = " ".join([p.text for p in paragraphs])
        else:
            # Fallback
            content = soup.find('div', id='content')
            content_text = content.text if content else ""

        list_of_words = self.raw_text_to_list(content_text)

        # Obsługa JSON (odczyt -> aktualizacja -> zapis)
        try:
            with open(WORD_COUNTS_FILE, 'r', encoding='utf-8') as f:
                dictionary = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            dictionary = {}

        for word in list_of_words:
            if word in dictionary:
                dictionary[word] += 1
            else:
                dictionary[word] = 1
        
        with open(WORD_COUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(dictionary, f, ensure_ascii=False)


class Controller:
    """
    Klasa kontrolująca działanie programu.
    """
    def __init__(self, args):
        self.args = args

    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser()
        parser.add_argument('--summary', type=str, help='podsumowanie pokemona')
        parser.add_argument('--table', type=str, help='fraza gdzie szukac tabeli')
        parser.add_argument('--number', type=int, help='ktora tabela')
        parser.add_argument('--first-row-is-header', action='store_true', help='czy ma byc z nagłówkiem')
        parser.add_argument('--count-words', type=str, help='liczy słowa')
        parser.add_argument('--analize-relative-word-frequency', action='store_true', help='analiza czestotliwosci')
        parser.add_argument('--mode', type=str, help='tryb analizowania article/language')
        parser.add_argument('--count', type=int, default=10, help='ile wyników pokazujemy w tabeli')
        parser.add_argument('--chart', type=str, help='sciezka do zapisu wykresu')
        parser.add_argument('--auto-count-words', type=str, help='fraza startowa crawlera')
        parser.add_argument('--depth', type=int, help='glebokosc szukania')
        parser.add_argument('--wait', type=float, help='czas oczekiwania')
        parser.add_argument('--local', action='store_true', help='uzyj pliku lokalnego')
        return parser.parse_args()

    def _fetch_soup(self, phrase: str) -> Optional[BeautifulSoup]:
        use_local = self.args.local
        scraper = Scraper(BULBAPEDIA_URL, phrase, use_local_file=use_local)
        return scraper.get_soup()

    def analyze_relative_word_frequency(self, mode: str, count: int, chart: str):
        """Funkcja analizująca relatywną częstość występowania słów."""
        try:
            with open(WORD_COUNTS_FILE, 'r', encoding='utf-8') as f:
                dictionary = json.load(f)
        except FileNotFoundError:
            print('Nie zebrano danych. Użyj --count-words lub --auto-count-words.')
            return

        try:
            top_wiki_word = top_n_list('en', 1)[0]
            max_freq_wiki = word_frequency(top_wiki_word, 'en')
        except Exception:
            max_freq_wiki = 1

        if not dictionary:
            print("Słownik jest pusty")
            return
            
        max_count_article = max(dictionary.values())
        data = []
        
        if mode == 'article':
            for word in dictionary:
                norm_art = dictionary[word] / max_count_article
                norm_wiki = word_frequency(word, 'en') / max_freq_wiki
                if norm_wiki == 0:
                    norm_wiki = 0.0
                
                data.append({
                    'word': word,
                    'frequency in the article': norm_art,
                    'frequency in wiki language': norm_wiki
                })
            df = pd.DataFrame(data)
            df = df.sort_values(by='frequency in the article', ascending=False)
            df = df.head(count)

        elif mode == 'language':
            top_words = top_n_list('en', count)
            
            for word in top_words:
                freq_lang = word_frequency(word, 'en')
                norm_wiki = freq_lang / max_freq_wiki
                
                if word in dictionary:
                    norm_art = dictionary[word] / max_count_article
                else:
                    norm_art = 0.0
                
                data.append({
                    'word': word,
                    'frequency in the article': norm_art,
                    'frequency in wiki language': norm_wiki
                })
            df = pd.DataFrame(data)
            df = df.sort_values(by='frequency in wiki language', ascending=False)
        else:
            print('Nieznany tryb (użyj article lub language)')
            return

        print(df)

        if chart:
            df_plot = df.set_index('word')
            df_plot.plot(kind='bar', figsize=(12, 6), color=['blue', 'red'])

            plt.title("Frequency of words on Wiki vs Global")
            plt.ylabel("Normalized Frequency")
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            try:
                plt.savefig(chart)
                print(f"Wykres zapisano do: {chart}")
            except Exception as e:
                print(f"Błąd zapisu wykresu: {e}")
            
            plt.show() 

    def is_valid_link(self, link: str) -> bool:
        if '/wiki/' in link and ':' not in link:
            return True
        return False
    
    def clean_link_phrase(self, link: str) -> str:
        new_phrase = link.split('/wiki/')[-1]
        new_phrase = new_phrase.split('#')[0]
        return new_phrase

    def auto_count_words(self, starting_phrase: str, depth: int, wait: float):
        """Crawler przechodzący automatycznie po linkach."""
        starting_phrase = starting_phrase.replace(' ', '_')
        queue = [starting_phrase]
        visited_sites = {starting_phrase: 0}
        
        idx = 0
        while idx < len(queue):
            phrase_curr = queue[idx]
            idx += 1
            
            depth_curr = visited_sites[phrase_curr]
            print(f'Przetwarzanie: {phrase_curr.replace("_", " ")}')
            
            soup = self._fetch_soup(phrase_curr)
            
            if soup:
                processor = SingleArticleProcessing(soup)
                # Tutaj następuje zapis do JSON wewnątrz metody
                processor.update_word_counts()

                if depth_curr < depth:
                    for link in soup.find_all('a', href=True):
                        href = link['href']

                        if self.is_valid_link(href):
                            new_phrase = self.clean_link_phrase(href)

                            if new_phrase not in visited_sites:
                                visited_sites[new_phrase] = depth_curr + 1
                                queue.append(new_phrase)
        
            if wait:
                time.sleep(wait)

    def run(self):
        args = self.args

        if args.summary:
            soup = self._fetch_soup(args.summary)
            if soup:
                processor = SingleArticleProcessing(soup)
                processor.process_summary()

        if args.table and args.number:
            soup = self._fetch_soup(args.table)
            if soup:
                processor = SingleArticleProcessing(soup)
                processor.process_table(args.table, args.number, args.first_row_is_header)

        if args.count_words:
            soup = self._fetch_soup(args.count_words)
            if soup:
                processor = SingleArticleProcessing(soup)
                processor.update_word_counts()

        if args.analize_relative_word_frequency and args.mode:
            self.analyze_relative_word_frequency(args.mode, args.count, args.chart)

        if args.auto_count_words and args.depth is not None:
            wait_time = args.wait if args.wait else 0.0
            self.auto_count_words(args.auto_count_words, args.depth, wait_time)


if __name__ == "__main__":
    # Opcjonalne ustawienie wyświetlania w pandas
    pd.set_option('display.max_rows', None)
    
    parsed_args = Controller.parse_arguments()
    controller = Controller(parsed_args)
    controller.run()