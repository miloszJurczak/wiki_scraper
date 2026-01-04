import argparse

import pytest
from bs4 import BeautifulSoup

from wiki_scraper import Controller, Scraper, SingleArticleProcessing


# Obiekt BeautifulSoup, który jest przykładową stroną html
@pytest.fixture
def example_soup():
    """Zwraca gotowy obiekt BeautifulSoup, a nie string."""
    html = """
    <div id="content" class="mw-body">
        <div class="noarticletext mw-content-ltr" dir="ltr" lang="pl">
            <p>
                Nic tutaj nie ma. To pusta strona testowa
            </p>
        </div>
    </div>
    """
    return BeautifulSoup(html, 'html.parser')


@pytest.fixture
def example_link():
    return 'bulbapedia.bulbagarden.net/wiki/X_Attack_(Next_Quest_8)'


# Tworzymy obiekt, który jest potrzebny do zainicjowania Controller-a
@pytest.fixture
def mock_arguments():
    return argparse.Namespace(local=False)


# Bierzemy zapisaną wcześniej stronę z Bulbapedii "Team Rocket" i wczytujemy ją
@pytest.fixture
def example_article():
    with open('Team_Rocket.html', 'r', encoding='utf-8') as f:
        site = f.read()
    return site


### === TESTY === ###


def test_check_if_exist(example_soup):
    """
    Poniższy test powinien zwrócić False, ponieważ w przykładowym obiekcie
    BeautifulSoup występuje: <div class="noarticletext mw-content-ltr">.
    """
    # Do SingleArticleProcessing możemy wrzucić None, bo i tak z tego nie korzystamy.
    # Processor to obiekt posiadający funkcję check_if_exist.
    processor = SingleArticleProcessing(None)  # noqa: F841 (zmienna nieużywana, ale zostawiam dla kontekstu)
    scraper = Scraper('https://testujemy', 'testy')
    
    # PEP 8: Porównania do False robimy przez 'assert not'
    assert not scraper.check_if_exist(example_soup)


def test_raw_text_to_list():
    # Do SingleArticleProcessing możemy wrzucić None, bo i tak z tego nie korzystamy.
    # Processor to obiekt posiadający funkcję raw_text_to_list.
    processor = SingleArticleProcessing(None)
    text = 'Nic tu nie ma. Pusta strona testowa'
    
    expected_answer = ['nic', 'tu', 'nie', 'ma', 'pusta', 'strona', 'testowa']
    function_answer = processor.raw_text_to_list(text)
    
    assert expected_answer == function_answer


def test_is_link_right(example_link):
    controller = Controller(None)
    # PEP 8: Porównania do True robimy bezpośrednio
    assert controller.is_link_right(example_link)


def test_delete_unimportant_parts(example_link):
    controller = Controller(None)
    assert controller.delete_unimportant_parts(example_link) == 'X_Attack_(Next_Quest_8)'