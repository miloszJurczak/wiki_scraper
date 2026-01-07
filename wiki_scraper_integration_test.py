import argparse
import os
import sys
from io import StringIO

from wiki_scraper import Controller

INPUT_FILE = 'Team_Rocket.html'
RESULT_FILE = 'TEST_RESULT.txt'


def test_table_function():
    test_state = False
    does_input_file_exist = True

    # Sprawdzenie czy istnieje plik wejściowy na dysku
    if not os.path.exists(INPUT_FILE):
        does_input_file_exist = False
        print('Nie znaleziono pliku wejściowego')

    assert does_input_file_exist

    # Sprawdzenie czy istnieje plik wynikowy. Jeśli istnieje - usuwa go
    if os.path.exists(RESULT_FILE):
        os.remove(RESULT_FILE)

    args = argparse.Namespace(
        summary='Team Rocket',
        table=None,
        first_row_is_header=False,
        number=None,
        count_words=None,
        analize_relative_word_frequency=None,
        mode=None,
        count=None,
        chart=None,
        auto_count_words=None,
        depth=None,
        wait=None,
        local=True
    )

    # Ręczne przekierowanie wyniku działania programu
    original_stdout = sys.stdout  # Obecne wyjście
    capture = StringIO()          # Bufor w pamięci
    sys.stdout = capture          # Podmieniamy wyjście na nasz bufor

    controller = Controller(args)
    controller.run()

    sys.stdout = original_stdout

    # Bierzemy to co wypluł program
    output = capture.getvalue()

    expected_start = "Team Rocket (Japanese:"
    expected_end = "in the Sevii Islands."

    if expected_start in output and expected_end in output:
        print('Test się udał!!!')
        test_state = True

    assert test_state


if __name__ == '__main__':
    test_table_function()