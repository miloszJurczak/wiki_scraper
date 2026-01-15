import argparse
import pytest
from bs4 import BeautifulSoup
from wiki_scraper import Controller, Scraper, SingleArticleProcessing

# === FIXTURES ===

@pytest.fixture
def example_soup():
    """Symulacja pustej strony do testów"""
    html = """
    <div id="content" class="mw-body">
        <div class="noarticletext mw-content-ltr" dir="ltr" lang="pl">
            <p>Nic tutaj nie ma. To pusta strona testowa</p>
        </div>
    </div>
    """
    return BeautifulSoup(html, 'html.parser')

@pytest.fixture
def example_link():
    """Zwraca poprawny link do testów"""
    return 'bulbapedia.bulbagarden.net/wiki/X_Attack_(Next_Quest_8)'

@pytest.fixture
def mock_arguments():
    """Mockowane argumenty z konsoli"""
    return argparse.Namespace(local=False)

@pytest.fixture
def example_article():
    """Wczytuje prawdziwy plik HTML z dysku"""
    with open('Team_Rocket.html', 'r', encoding='utf-8') as f:
        site = f.read()
    return site


# === TESTY ===

def test_check_if_exist(example_soup):
    """Sprawdza, czy scraper poprawnie wykrywa nieistniejącą stronę"""
    processor = SingleArticleProcessing(None)
    scraper = Scraper('https://testujemy', 'testy')
    assert not scraper.check_if_exist(example_soup)


def test_raw_text_to_list():
    """Testuje czyszczenie tekstu i zamianę na listę słów"""
    processor = SingleArticleProcessing(None)
    text = 'Nic tu nie ma. Pusta strona testowa'
    
    expected_answer = ['nic', 'tu', 'nie', 'ma', 'pusta', 'strona', 'testowa']
    function_answer = processor.raw_text_to_list(text)
    
    assert expected_answer == function_answer


def test_is_link_right(example_link):
    """Weryfikuje, czy podany link jest poprawny"""
    controller = Controller(None)
    assert controller.is_link_right(example_link)


def test_delete_unimportant_parts(example_link):
    """Sprawdza wycinanie samego tytułu artykułu z adresu URL"""
    controller = Controller(None)
    assert controller.delete_unimportant_parts(example_link) == 'X_Attack_(Next_Quest_8)'
