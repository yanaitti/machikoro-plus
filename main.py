from flask import Flask, Response, render_template
from flask_caching import Cache
import uuid
import random
import collections
import json
import os
import copy
import numpy as np

app = Flask(__name__)


# Cacheインスタンスの作成
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379'),
    'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 2,
})


'''
ext
'': 基本ルール(場に全部カード出す)
'ext': 拡張ルール(場に10種類のみ。10種類未満になったら、カードを引く)

type
    0: ランドマーク
    1: 自分のターン
    2: 他人ののターン
    3: 誰でも
cost コイン数
score 出目
'''

mastercards = [
    {'name': '駅', 'type': 0, 'cost':4, 'style': 'ランドマーク', 'pack': 0},
    {'name': 'ショッピングモール', 'type': 0, 'cost':10, 'style': 'ランドマーク', 'pack': 0},
    {'name': '遊園地', 'type': 0, 'cost': 16, 'style': 'ランドマーク', 'pack': 0},
    {'name': '電波塔', 'type': 0, 'cost': 22, 'style': 'ランドマーク', 'pack': 0},

    {'name': '麦畑', 'type': 3, 'cost': 1, 'score': '1', 'stock': 6, 'get': 1, 'style': '農園', 'pack': 0},
    {'name': '牧場', 'type': 3, 'cost': 1, 'score': '2', 'stock': 6, 'get': 1, 'style': '牧場', 'pack': 0},
    {'name': 'パン屋', 'type': 1, 'cost': 1, 'score': '2-3', 'stock': 6, 'get': 1, 'style': '商店', 'pack': 0},
    {'name': 'カフェ', 'type': 2, 'cost': 2, 'score': '3', 'stock': 6, 'get': 1, 'style': '飲食店', 'pack': 0},
    {'name': 'コンビニ', 'type': 1, 'cost': 2, 'score': '4', 'stock': 6, 'get': 3, 'style': '商店', 'pack': 0},
    {'name': '森林', 'type': 3, 'cost': 3, 'score': '5', 'stock': 6, 'get': 1, 'style': '自然', 'pack': 0},
    {'name': 'チーズ工場', 'type': 1, 'cost': 5, 'score': '7', 'stock': 6, 'get': 3, 'style': '工場', 'pack': 0},
    {'name': '家具工場', 'type': 1, 'cost': 3, 'score': '8', 'stock': 6, 'get': 3, 'style': '工場', 'pack': 0},
    {'name': '鉱山', 'type': 3, 'cost': 6, 'score': '9', 'stock': 6, 'get': 5, 'style': '自然', 'pack': 0},
    {'name': 'ファミレス', 'type': 2, 'cost': 3, 'score': '9-10', 'stock': 6, 'get': 2, 'style': '飲食店', 'pack': 0},
    {'name': 'リンゴ園', 'type': 3, 'cost': 3, 'score': '10', 'stock': 6, 'get': 3, 'style': '農園', 'pack': 0},
    {'name': '青果市場', 'type': 1, 'cost': 2, 'score': '11-12', 'stock': 6, 'get': 2, 'style': '市場', 'pack': 0},

    {'name': 'スタジアム', 'type': 1, 'cost': 6, 'score': '6', 'stock': 4, 'get': 2, 'style': 'ランドマーク', 'pack': 0},
    {'name': 'テレビ局', 'type': 1, 'cost': 6, 'score': '6', 'stock': 4, 'get': 5, 'style': 'ランドマーク', 'pack': 0},
    {'name': 'ビジネスセンター', 'type': 1, 'cost': 1, 'score': '6', 'stock': 4, 'get': 0, 'style': 'ランドマーク', 'pack': 0},
]


@app.route('/')
def homepage():
    return render_template('index.html')


# create the game group
@app.route('/create')
@app.route('/create/<nickname>')
def create_game(nickname=''):
    game = {
        'status': 'waiting',
        'stocks': [],
        'coin_diff': [],
        'boardcards': [],
        'dice': 0,
        'players': []}
    player = {}

    gameid = str(uuid.uuid4())
    game['gameid'] = gameid
    player['playerid'] = gameid
    player['nickname'] = nickname if nickname != '' else gameid
    player['landmarks'] = []
    player['facilities'] = []
    player['dices'] = 1
    game['players'].append(player)

    app.logger.debug(gameid)
    app.logger.debug(game)
    cache.set(gameid, game)
    return gameid


# join the game
@app.route('/<gameid>/join')
@app.route('/<gameid>/join/<nickname>')
def join_game(gameid, nickname='default'):
    game = cache.get(gameid)
    if game['status'] == 'waiting':
        player = {}

        playerid = str(uuid.uuid4())
        player['playerid'] = playerid
        if nickname == 'default':
            player['nickname'] = playerid
        else:
            player['nickname'] = nickname

        player['landmarks'] = []
        player['facilities'] = []
        player['dice'] = 1
        game['players'].append(player)

        cache.set(gameid, game)

        return json.dumps(player)
    else:
        return 'Already started'


# start the game
@app.route('/<gameid>/start/<int:pack>')
@app.route('/<gameid>/start/<int:pack>/<ext>')
def start_game(gameid, pack, ext=''):
    game = cache.get(gameid)
    app.logger.debug(gameid)
    app.logger.debug(game)
    game['status'] = 'started'
    game['ext'] = ext

    # initial card setting
    stocks = []
    boardcards = []

    _mastercards = [_mastercard for _mastercard in mastercards if _mastercard['pack'] <= pack]
    if game['ext'] == 'ext':
        for mastercard in _mastercards:
            app.logger.debug(mastercard)
            if mastercard['type'] > 0:
                boardcards.append({'name': mastercard['name'], 'cnt': 0, 'cost': mastercard['cost']})
                mCnt = mastercard['stock']
                for i in list(range(mCnt)):
                    stocks.append(mastercard)

        random.shuffle(stocks)

        while len([_boardcard for _boardcard in boardcards if _boardcard['cnt'] > 0]) < 10 and len(stocks) > 0:
            mastercard = stocks.pop(0)
            boardcard = [_boardcard for _boardcard in boardcards if _boardcard['name'] == mastercard['name']][0]
            boardcard['cnt'] += 1
    else:
        for mastercard in _mastercards:
            app.logger.debug(mastercard)
            if mastercard['type'] > 0:
                boardcards.append({'name': mastercard['name'], 'cnt': mastercard['stock'], 'cost': mastercard['cost']})


    # initialize for each players
    for player in game['players']:
        player['facilities'] = []
        player['landmarks'] = []

        player['facilities'].append(_mastercards[4])
        player['facilities'].append(_mastercards[5])
        player['coins'] = 3

        for mastercard in _mastercards:
            if mastercard['type'] == 0:
                landmark = copy.deepcopy(mastercard)
                landmark['turn'] = False
                player['landmarks'].append(landmark)

    game['mastercards'] = _mastercards
    game['stocks'] = stocks
    game['boardcards'] = boardcards

    cache.set(gameid, game)
    return 'ok'


# buy the card
@app.route('/<gameid>/<playerid>/buy/facility/<int:facilityid>')
def buy_card(gameid, playerid, facilityid):
    game = cache.get(gameid)

    _mastercards = game['mastercards']
    player = [_player for _player in game['players'] if _player['playerid'] == playerid][0]
    boardcard = game['boardcards'][facilityid]
    mastercard = [_mastercard for _mastercard in _mastercards if _mastercard['name'] == boardcard['name']][0]

    if player['coins'] < boardcard['cost']:
        return 'ng cost'

    if boardcard['cnt'] == 0:
        return 'ng cnt'

    player['coins'] -= boardcard['cost']
    player['facilities'].append(mastercard)
    boardcard['cnt'] -= 1

    stocks = game['stocks']
    boardcards = game['boardcards']

    while len([_boardcard for _boardcard in boardcards if _boardcard['cnt'] > 0]) < 10 and len(stocks) > 0:
        mastercard = stocks.pop(0)
        boardcard = [_boardcard for _boardcard in boardcards if _boardcard['name'] == mastercard['name']][0]
        boardcard['cnt'] += 1

    game['boardcards'] = boardcards
    game['stocks'] = stocks

    cache.set(gameid, game)
    return 'ok'


# buy the landmark
@app.route('/<gameid>/<playerid>/buy/landmark/<int:landmarkid>')
def buy_landmark(gameid, playerid, landmarkid):
    game = cache.get(gameid)
    player = [_player for _player in game['players'] if _player['playerid'] == playerid][0]
    landmark = player['landmarks'][landmarkid]

    if player['coins'] < landmark['cost']:
        return 'ng'

    player['coins'] -= landmark['cost']
    landmark['turn'] = True

    if len(player['landmarks']) == 4:
        game['status'] = 'end'

    cache.set(gameid, game)
    return 'ok'


# dice to roll
@app.route('/<gameid>/roll/<int:rollcnt>')
def dice_roll(gameid, rollcnt):
    game = cache.get(gameid)

    dice = []
    if rollcnt == 2:
        dice.append(random.randint(1, 6))
        dice.append(random.randint(1, 6))
    else:
        dice.append(random.randint(1, 6))

    game['dice'] = dice

    cache.set(gameid, game)
    return str(dice)


# trade the card
@app.route('/<gameid>/<playerid>/trade/<toplayerid>/<int:cardnum>/<int:tocardnum>')
def trade_card(gameid, playerid, toplayerid, cardnum, tocardnum):
    game = cache.get(gameid)

    player = [_player for _player in game['players'] if _player['playerid'] == playerid][0]
    facility = player['facilities'].pop(cardnum)

    toplayer = [_player for _player in game['players'] if _player['playerid'] == toplayerid][0]
    tofacility = toplayer['facilities'].pop(tocardnum)

    player['facilities'].append(tofacility)
    toplayer['facilities'].append(facility)

    cache.set(gameid, game)
    return 'ok'


# choice the player
@app.route('/<gameid>/<playerid>/choice/<fromplayerid>')
def choice_player(gameid, playerid, fromplayerid):
    game = cache.get(gameid)

    player = [_player for _player in game['players'] if _player['playerid'] == playerid][0]
    fromplayer = [_player for _player in game['players'] if _player['playerid'] == fromplayerid][0]

    if fromplayer['coins'] > 5:
        player['coins'] += 5
        fromplayer['coins'] -= 5
    else:
        player['coins'] += fromplayer['coins']
        fromplayer['coins'] = 0

    cache.set(gameid, game)
    return 'ok'


# judgement for dice
@app.route('/<gameid>/judgement/<int:dice>')
def judgement_dice(gameid, dice):
    game = cache.get(gameid)

    player = game['players'][0]
    mycoin = player['coins']
    retCd = 'ok'

    results = np.zeros(len(game['players'])).tolist()

    # judgement process
    # 他人のターン
    for pIdx, _player in enumerate(game['players']):
        coins = 0
        if _player['playerid'] != player['playerid']:
            yourselfcards = [_card for _card in _player['facilities'] if _card['type'] == 2]
            for card in yourselfcards:
                getcoin = card['get'] + 1 if _player['landmarks'][1]['turn'] == True and card['style'] in ['飲食店', '商店'] else card['get']
                diff = 0
                scores = [int(_score) for _score in card['score'].split('-')]
                if len(scores) == 1:
                    if scores[0] == dice:
                        diff = getcoin if player['coins'] > getcoin else player['coins']
                else:
                    if scores[0] <= dice <= scores[1]:
                        diff = getcoin if player['coins'] > getcoin else player['coins']
                player['coins'] -= diff
                results[0] -= diff
                _player['coins'] += diff
                coins += diff

        results[pIdx] += coins

    # 自分のターン
    coins = 0
    myselfcards = [_card for _card in player['facilities'] if _card['type'] == 1]
    for card in myselfcards:
        # getcoin = card['get']
        getcoin = card['get'] + 1 if player['landmarks'][1]['turn'] == True and card['style'] in ['飲食店', '商店'] else card['get']
        diff = 0
        scores = [int(_score) for _score in card['score'].split('-')]
        if len(scores) == 1:
            if scores[0] == dice:
                diff = getcoin
        else:
            if scores[0] <= dice <= scores[1]:
                diff = getcoin

        if card['name'] == 'チーズ工場':
            diff *= len([_card for _card in player['facilities'] if _card['style'] == '牧場'])
            player['coins'] += diff
        elif card['name'] == '家具工場':
            diff *= len([_card for _card in player['facilities'] if _card['style'] == '自然'])
            player['coins'] += diff
        elif card['name'] == '青果市場':
            diff *= len([_card for _card in player['facilities'] if _card['style'] == '農園'])
            player['coins'] += diff
        elif card['name'] == 'スタジアム':
            # 効果：（自分のターン）全員から２コインもらう
            for pIdx, _player in enumerate(game['players']):
                tmp_coin = 0
                if _player['playerid'] != player['playerid']:
                    tmp_coin = getcoin if _player['coins'] > getcoin else _player['coins']
                    _player['coins'] -= tmp_coin
                    player['coins'] += tmp_coin
                    results[pIdx] -= tmp_coin
                    diff += tmp_coin
        elif card['name'] == 'テレビ局':
            # 効果：（自分のターン）任意のプレイヤーから５コインもらう
            diff = 0
            retCd = 'choicePlayer'
        elif card['name'] == 'ビジネスセンター':
            # 効果：（自分のターン）大施設以外の施設１軒を他プレイヤーと交換できる
            diff = 0
            retCd = 'tradeCard'
        else:
            player['coins'] += diff

        coins += diff

    results[0] += coins

    # 誰のターンでも
    for pIdx, _player in enumerate(game['players']):
        coins = 0
        anyonecards = [_card for _card in _player['facilities'] if _card['type'] == 3]
        for card in anyonecards:
            diff = 0
            scores = [int(_score) for _score in card['score'].split('-')]
            if len(scores) == 1:
                if scores[0] == dice:
                    diff = card['get']
            else:
                if scores[0] <= dice <= scores[1]:
                    diff = card['get']
            coins += diff

        _player['coins'] += coins
        results[pIdx] += coins

    game['coin_diff'] = results

    cache.set(gameid, game)
    return retCd


# next to player
@app.route('/<gameid>/next')
def next_player(gameid):
    game = cache.get(gameid)

    # game['routeidx'] = (game['routeidx'] + 1) % len(game['players'])
    game['players'] = np.roll(np.array(game['players']), -1).tolist()

    cache.set(gameid, game)
    return 'ok'


# all status the game
@app.route('/<gameid>/status')
def game_status(gameid):
    game = cache.get(gameid)

    return json.dumps(game)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    # app.run(debug=True)
