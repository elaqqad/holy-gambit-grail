from io import StringIO
import os
from time import sleep
import chess.pgn
import csv
import json
import requests
import re
import urllib
import chess
import chess.engine


CHESS_OPENINGS_URL = r'https://raw.githubusercontent.com/lichess-org/chess-openings/master'
MASTERS_EXPLORER = r'https://explorer.lichess.ovh/masters?play='
LICHESS_EXPLORER = r'https://explorer.lichess.ovh/lichess?variant=standard&speeds=blitz,rapid,classical&ratings=1800,2000,2200,2500&fen='
STOCKFISH_PATH = r''
OPENINGS_START = ['a', 'b', 'c', 'd', 'e']


def choose_top_game(games, winner):
    won_games = [game for game in games if game['winner'] == winner]
    if len(won_games) > 0:
        return won_games[0]['id']
    if len(won_games) > 0:
        return won_games[0]['id']
    return None


def make_api_call(url):
    # sleep(1)
    # print(url)
    headers = {
        'Accept': 'application/x-ndjson'
        # 'Authorization': 'Bearer ' + os.environ['LICHESS_API_TOKEN']
    }
    response = requests.get(url, headers=headers)
    try:
        return response.json()
    except Exception as error:
        print(error)
        print(response.reason)
        print(response.status_code)
        print(response.content)
        return {
            'white': 0,
            'draws': 0,
            'black': 0,
            'topGames': []
        }


def get_lichess_game(fen, winner):
    url = f'{LICHESS_EXPLORER}{urllib.parse.quote(fen)}'
    json_response = make_api_call(url)
    chosen_game = choose_top_game(json_response['topGames'], winner)
    return {
        'white': json_response['white'],
        'draws': json_response['draws'],
        'black': json_response['black'],
        'game': chosen_game
    }


def get_master_game(algebraic, winner):
    url = f'{MASTERS_EXPLORER}{",".join(algebraic)}'
    json_response = make_api_call(url)
    return choose_top_game(json_response['topGames'], winner)


def is_gambit(name: str):
    return name.strip().lower().endswith('gambit')


def analyse(pgn: str, name: str, engine: chess.engine.SimpleEngine):
    split = re.split(r'\d*\.', pgn)
    game = chess.pgn.read_game(StringIO(pgn))
    while not game.is_end():
        game = game.next()
    board = game.board()
    fen = board.fen()
    algebraic = list(map(lambda m: m.uci(), board.move_stack))
    color_gambit = 'black' if ' ' in split[-1].strip() else 'white'
    move_number = 2 * \
        (len(split)-1) if color_gambit == 'black' else 2*(len(split)-1)-1
    master_game = get_master_game(algebraic, color_gambit)
    lichess_game = get_lichess_game(fen, color_gambit)
    if engine is not None :
        result = engine.analyse(board, chess.engine.Limit(time=5))
        if(result['score'].relative <= chess.engine.Cp(0)) :
            print(f'Suspicious gambit {name} {result["score"]}, https://lichess.org/{lichess_game["game"]}/{color_gambit}#{move_number}, {fen}')
    return {
        'move': move_number,
        'color': color_gambit,
        'fen': fen,
        'master': master_game,
        'lichess': lichess_game['game'],
        'white': lichess_game['white'],
        'draws': lichess_game['draws'],
        'black': lichess_game['black'],
    }


if __name__ == '__main__':
    if '' != STOCKFISH_PATH and None != STOCKFISH_PATH:
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    else :
        engine = None
    # Used for testing with small numbers
    number_of_gambits = 1000
    gambits = []
    for letter in OPENINGS_START:
        openings_page = requests.get(f'{CHESS_OPENINGS_URL}/{letter}.tsv')
        openings_lines = openings_page.iter_lines(decode_unicode=True)
        tsv_reader = csv.reader(openings_lines, delimiter='\t')
        next(tsv_reader)  # Ignore header
        for row in tsv_reader:
            if(len(gambits) >= number_of_gambits) :
                break
            if is_gambit(row[1]):
                analysis = analyse(row[2], row[1], engine)
                opening_gambit = {
                    'eco': row[0],
                    'name': row[1],
                    'pgn': row[2],
                    'move': analysis['move'],
                    'color': analysis['color'],
                    'fen': analysis['fen'],
                    'master': analysis['master'],
                    'lichess': analysis['lichess'],
                    'white': analysis['white'],
                    'draws': analysis['draws'],
                    'black': analysis['black'],
                }
                print(f'{len(gambits)} : {opening_gambit["name"]}')
                gambits.append(opening_gambit)
        if(len(gambits) >= number_of_gambits) :
            break
    with open('gambits.json', 'w') as json_file:
        json.dump(gambits, json_file)
    with open('gambits.csv', 'w', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        keys = list(gambits[0].keys())
        writer.writerow(keys)
        for gambit in gambits:
            writer.writerow([gambit[key] for key in keys])
    if engine is not None :
        engine.close()
