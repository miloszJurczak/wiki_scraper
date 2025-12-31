import sys
import argparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
from wordfreq import word_frequency, top_n_list
import time

#domyślny URL do bulbapedii
BULBAPEDIA_URL = 'https://bulbapedia.bulbagarden.net/wiki/'

#klasa scrapera
class Scraper:
    def __init__(self, base_url, phrase, use_local_file=False):
        self.base_url = base_url
        self.phrase = phrase
        self.use_local_file = use_local_file

    #sprawdza czy podana strona istnieje. Jeśli istnieje zwraca False, jeśli nie istnieje True
    #dodatkowo wyświetla informacje i tekst z noarticle
    def check_if_exist(self, soup):
        location_not_found = soup.find('div', class_='noarticletext mw-content-ltr')
        if location_not_found:
            paragraph = location_not_found.find('p')

            if paragraph:
                error_message = paragraph.get_text(separator=' ', strip=True)
                print(f'Strona nie istnieje. Tekst błędu strony:\n{error_message}')
                return False
        return True

    def get_soup(self):
        argument = self.phrase.replace(' ', '_')

        #obsługa pliku lokalnego
        if self.use_local_file:
            try:
                with open(f"{argument}.html", 'r', encoding='utf-8') as f:
                    return BeautifulSoup(f, 'html.parser')
            except FileNotFoundError:
                print(f"nie znalazłem pliku lokalnego: {argument}.html")
                return None

        response = requests.get(f'{self.base_url}{argument}')
        soup = BeautifulSoup(response.text, 'html.parser')

        #Sprawdza czy podana strona nie jest niezapisana:
        location_not_found = soup.find('div', class_='noarticletext mw-content-ltr')
        if self.check_if_exist(soup):
            return soup
        else: return None

class SingleArticleProcessing:
    """
    Klasa odpowiedzialna za procesowanie i operacje na pojedyńczym podanym artykule
    """
    def __init__(self, soup):
        self.soup = soup

    #funkcja odpowiedzialna za wyświetlenie podsumowania
    def summary_function(self):
        soup = self.soup 

        #Wyświetla pierwszy paragraf strony z --summary:
        locations_first_paragraph = soup.find('div', class_="mw-content-ltr mw-parser-output")
        
        #Zabezpieczenie gdyby div nie istniał:
        if locations_first_paragraph:
            paragraph = locations_first_paragraph.find('p')
            
            #dodatkowo sprawdzamy czu paragraf został znaleziony
            if paragraph:
                final_first_paragraph = ' '.join(paragraph.text.split())
                print(final_first_paragraph)
            else:
                print("Nie znaleziono paragrafu!")
        else:
            print("Nie znaleziono treści!")
        
        return final_first_paragraph

    #funkcja odpowiedzialna za wyświetlenie wskazanej tabeli
    def table_function(self, argument_name, number_of_table, header):
        soup = self.soup
        
        all_tables = soup.find_all('table')
        if number_of_table > len(all_tables):
            print(f"nie znaleziono tabeli o podanym numerze")
            return

        index = number_of_table - 1
        table = all_tables[index]
        
        #robimy tabelę ręcznie, aby pominąć obrazki i mieć pełną kontrolę
        table_data = []
        rows = table.find_all('tr')
        for row in rows:
            row_data = []
            #th - nagłówki, tr - komórki
            #recursive=False gwarantuje że nie pobierzemy śmieci z zagnieżdżonych tabel
            cells = row.find_all(['td', 'th'], recursive=False)

            for cell in cells:
                clean_cell_text = cell.get_text(separator=' ', strip=True)
                row_data.append(clean_cell_text)
            
            #dodajemy wiersz do danych jeśli nie jest pusty
            if row_data:
                table_data.append(row_data)

        df = pd.DataFrame(table_data)
        
        #domyślnie nie zapisujemy nagłówka w pliku
        write_header = False

        if header:
            #sprawdzamy czy pierwszy wiersz nadaje się na nagłówek
            #musi mieć tyle samo kolumn, ile ma najszerszy wiersz w tabeli
            num_columns_data = df.shape[1]
            if len(table_data) > 0:
                num_columns_header = len(table_data[0])

                if num_columns_header == num_columns_data:
                    #pierwszy wiersz pasuje szerokością do reszty
                    new_header = df.iloc[0]
                    df = df[1:]
                    df.columns = new_header
                    write_header = True
                else:
                    #nagłówek jest krótszy niż dane
                    print(f"Pierwszy wiersz ma {num_columns_header} kolumn, "
                        f"a dane mają {num_columns_data}, "
                        "czyli pomijam ustawianie pierwszego wiersza jako nagłówka.")

        filename = f"{argument_name.replace(' ', '_')}.csv"
        df.to_csv(filename, index=False, header=write_header, encoding='utf-8-sig')
        
        print(f"Zapisano do: {filename}")
        print(df)

class Controller:
    """
    Klasa kontrolująca działanie programu, parsuje argumenty.
    Zawiera funkcje niewymagające pobierania strony
    """
    def __init__(self, args):
        self.args = args

    #funkcja parsująca argumenty
    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser()
        parser.add_argument('--summary', type=str, help='podsumowanie pokemona')
        parser.add_argument('--table', type=str, help='fraza gdzie szukac tabeli')
        parser.add_argument('--number', type=int, help='ktora tabela')
        parser.add_argument('--first-row-is-header', action='store_true', help='czy ma byc z nagłówkiem')
        #argument pozwalający na testowanie lokalne
        parser.add_argument('--local', action='store_true', help='uzyj pliku lokalnego zamiast sieci')
        return parser.parse_args()

    #metoda pomocnicza tworząca Scrapera
    def _fetch_soup(self, phrase):
        use_local = self.args.local
        #tworzymy scraper dla konkretnej frazy
        scraper = Scraper(BULBAPEDIA_URL, phrase, use_local_file=use_local)
        return scraper.get_soup()

    #Główna metoda uruchamiająca
    def run(self):
        args = self.args

        if args.summary:
            soup = self._fetch_soup(args.summary)
            if soup:
                processor = SingleArticleProcessing(soup)
                processor.summary_function()

        if args.table and args.number:
            soup = self._fetch_soup(args.table)
            if soup:
                processor = SingleArticleProcessing(soup)
                processor.table_function(args.table, args.number, args.first_row_is_header)

#blok uruchomieniowyw
if __name__ == "__main__":
    parsed_args = Controller.parse_arguments()
    controller = Controller(parsed_args)
    controller.run()