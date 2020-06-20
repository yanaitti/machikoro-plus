from flask import Flask, Response, render_template, url_for
from flask_caching import Cache
import uuid
import random
import collections
import json
import os
import copy
import numpy as np
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


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

bug:
ビジネスセンターが動かない（エラーが出た）
'''

mastercards = [
## 街コロ
    {'name': '駅', 'type': 0, 'cost':4, 'style': 'ランドマーク', 'pack': 0, 'available': True},
    {'name': 'ショッピングモール', 'type': 0, 'cost':10, 'style': 'ランドマーク', 'pack': 0, 'available': True},
    {'name': '遊園地', 'type': 0, 'cost': 16, 'style': 'ランドマーク', 'pack': 0, 'available': True},
    {'name': '電波塔', 'type': 0, 'cost': 22, 'style': 'ランドマーク', 'pack': 0, 'available': True},

    {'name': '麦畑', 'type': 3, 'cost': 1, 'score': '1', 'stock': 6, 'get': 1, 'style': '農園', 'pack': 0, 'available': True},
    {'name': '牧場', 'type': 3, 'cost': 1, 'score': '2', 'stock': 6, 'get': 1, 'style': '牧場', 'pack': 0, 'available': True},
    {'name': 'パン屋', 'type': 1, 'cost': 1, 'score': '2-3', 'stock': 6, 'get': 1, 'style': '商店', 'pack': 0, 'available': True},
    {'name': 'カフェ', 'type': 2, 'cost': 2, 'score': '3', 'stock': 6, 'get': 1, 'style': '飲食店', 'pack': 0, 'available': True},
    {'name': 'コンビニ', 'type': 1, 'cost': 2, 'score': '4', 'stock': 6, 'get': 3, 'style': '商店', 'pack': 0, 'available': True},
    {'name': '森林', 'type': 3, 'cost': 3, 'score': '5', 'stock': 6, 'get': 1, 'style': '自然', 'pack': 0, 'available': True},
    {'name': 'チーズ工場', 'type': 1, 'cost': 5, 'score': '7', 'stock': 6, 'get': 3, 'style': '工場', 'pack': 0, 'available': True},
    {'name': '家具工場', 'type': 1, 'cost': 3, 'score': '8', 'stock': 6, 'get': 3, 'style': '工場', 'pack': 0, 'available': True},
    {'name': '鉱山', 'type': 3, 'cost': 6, 'score': '9', 'stock': 6, 'get': 5, 'style': '自然', 'pack': 0, 'available': True},
    {'name': 'ファミレス', 'type': 2, 'cost': 3, 'score': '9-10', 'stock': 6, 'get': 2, 'style': '飲食店', 'pack': 0, 'available': True},
    {'name': 'リンゴ園', 'type': 3, 'cost': 3, 'score': '10', 'stock': 6, 'get': 3, 'style': '農園', 'pack': 0, 'available': True},
    {'name': '青果市場', 'type': 1, 'cost': 2, 'score': '11-12', 'stock': 6, 'get': 2, 'style': '市場', 'pack': 0, 'available': True},

    {'name': 'スタジアム', 'type': 1, 'cost': 6, 'score': '6', 'stock': 4, 'get': 2, 'style': 'ランドマーク', 'pack': 0, 'available': True},
    {'name': 'テレビ局', 'type': 1, 'cost': 6, 'score': '6', 'stock': 4, 'get': 5, 'style': 'ランドマーク', 'pack': 0, 'available': True},
    {'name': 'ビジネスセンター', 'type': 1, 'cost': 6, 'score': '6', 'stock': 4, 'get': 0, 'style': 'ランドマーク', 'pack': 0, 'available': True},

## 街コロ＋（プラス）
    {'name': '役所', 'type': 0, 'cost':0, 'style': 'ランドマーク', 'pack': 1, 'available': True},
    {'name': '港', 'type': 0, 'cost':2, 'style': 'ランドマーク', 'pack': 1, 'available': True},
    {'name': '空港', 'type': 0, 'cost': 30, 'style': 'ランドマーク', 'pack': 1, 'available': True},

    {'name': '寿司屋', 'type': 2, 'cost': 1, 'score': '1', 'stock': 6, 'get': 3, 'style': '飲食店', 'pack': 1, 'available': True},
    {'name': '花畑', 'type': 3, 'cost': 2, 'score': '4', 'stock': 6, 'get': 2, 'style': '農園', 'pack': 1, 'available': True},
    {'name': 'フラワーショップ', 'type': 1, 'cost': 1, 'score': '6', 'stock': 6, 'get': 1, 'style': '商店', 'pack': 1, 'available': True},
    {'name': 'ピザ屋', 'type': 2, 'cost': 1, 'score': '7', 'stock': 6, 'get': 1, 'style': '飲食店', 'pack': 1, 'available': True},
    {'name': 'バーガーショップ', 'type': 2, 'cost': 1, 'score': '8', 'stock': 6, 'get': 1, 'style': '飲食店', 'pack': 1, 'available': True},
    {'name': 'サンマ漁船', 'type': 3, 'cost': 2, 'score': '8', 'stock': 6, 'get': 3, 'style': '漁船', 'pack': 1, 'available': True},
    {'name': '食品倉庫', 'type': 1, 'cost': 2, 'score': '12-13', 'stock': 6, 'get': 2, 'style': '工場', 'pack': 1, 'available': True},
    {'name': 'マグロ漁船', 'type': 3, 'cost': 5, 'score': '12-14', 'stock': 6, 'get': 0, 'style': '漁船', 'pack': 1, 'available': False},

    {'name': '出版社', 'type': 1, 'cost': 5, 'score': '7', 'stock': 4, 'get': 1, 'style': 'ランドマーク', 'pack': 1, 'available': False},
    {'name': '税務署', 'type': 1, 'cost': 4, 'score': '8-9', 'stock': 4, 'get': 0, 'style': 'ランドマーク', 'pack': 1, 'available': False},

## 街コロシャープ
    {'name': '雑貨屋', 'type': 2, 'cost': 0, 'score': '2', 'stock': 6, 'get': 1, 'style': '飲食店', 'pack': 2, 'available': True},
    {'name': 'コーン畑', 'type': 2, 'cost': 2, 'score': '3-4', 'stock': 6, 'get': 1, 'style': '農園', 'pack': 2, 'available': True},
    {'name': '改装屋', 'type': 2, 'cost': 1, 'score': '4', 'stock': 6, 'get': 8, 'style': '業者', 'pack': 2, 'available': False},
    {'name': '高級フレンチ', 'type': 2, 'cost': 3, 'score': '5', 'stock': 6, 'get': 5, 'style': '飲食店', 'pack': 2, 'available': True},
    {'name': '賃金業', 'type': 2, 'cost': 0, 'score': '5-6', 'stock': 6, 'get': 2, 'style': '業者', 'pack': 2, 'available': False},
    {'name': 'ブドウ園', 'type': 2, 'cost': 3, 'score': '7', 'stock': 6, 'get': 3, 'style': '農園', 'pack': 2, 'available': True},
    {'name': 'ワイナリー', 'type': 2, 'cost': 3, 'score': '9', 'stock': 6, 'get': 6, 'style': '工場', 'pack': 2, 'available': False},
    {'name': '引越し屋', 'type': 2, 'cost': 2, 'score': '9-10', 'stock': 6, 'get': 4, 'style': '業者', 'pack': 2, 'available': False},
    {'name': 'ドリンク工場', 'type': 2, 'cost': 5, 'score': '11', 'stock': 6, 'get': 1, 'style': '工場', 'pack': 2, 'available': True},
    {'name': '会員制ＢＡＲ', 'type': 2, 'cost': 4, 'score': '12-14', 'stock': 6, 'get': 0, 'style': '飲食店', 'pack': 2, 'available': True},

    {'name': '清掃業', 'type': 1, 'cost': 4, 'score': '8', 'stock': 4, 'get': 0, 'style': 'ランドマーク', 'pack': 2, 'available': False},
    {'name': 'ＩＴベンチャー', 'type': 1, 'cost': 1, 'score': '10', 'stock': 4, 'get': 1, 'style': 'ランドマーク', 'pack': 2, 'available': False},
    {'name': '公園', 'type': 1, 'cost': 3, 'score': '11-13', 'stock': 4, 'get': 0, 'style': 'ランドマーク', 'pack': 2, 'available': False},
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
        'dice': [],
        'pack': 0,
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
        player['dices'] = 1
        game['players'].append(player)

        cache.set(gameid, game)

        # return json.dumps(player)
        return playerid + ' ,' + player['nickname'] + ' ,' + game['status']
    else:
        return 'Already started'


# get available cards list the game
@app.route('/<gameid>/availablelists/<int:pack>')
def get_availablelists(gameid, pack):
    game = cache.get(gameid)
    pakaging_cards = []

    pakaging_cards = [_mastercard for _mastercard in mastercards if _mastercard['pack'] <= pack]

    game['pack'] = pack

    cache.set(gameid, game)
    return json.dumps(pakaging_cards)


# set up cards list the game
@app.route('/<gameid>/setup/<selectcards>')
def setup_game(gameid, selectcards):
    game = cache.get(gameid)

    pack = game['pack']
    select_cards = selectcards.split(',')

    pakaging_cards = [_mastercard for _mastercard in mastercards if _mastercard['pack'] <= pack]
    selected_cards = [_mastercard for _mIdx, _mastercard in enumerate(pakaging_cards) if str(_mIdx) in select_cards]

    game['mastercards'] = selected_cards

    cache.set(gameid, game)
    return json.dumps(selected_cards)
    # return json.dumps(select_cards)


# start the game
@app.route('/<gameid>/start')
@app.route('/<gameid>/start/<ext>')
def start_game(gameid, ext=''):
    game = cache.get(gameid)
    app.logger.debug(gameid)
    app.logger.debug(game)
    game['status'] = 'started'
    game['ext'] = ext
    pack = game['pack']

    # initial card setting
    stocks = []
    boardcards = []

    # _mastercards = [_mastercard for _mastercard in mastercards if _mastercard['pack'] <= pack]
    _mastercards = [_mastercard for _mastercard in game['mastercards'] if _mastercard['pack'] <= pack]
    if game['ext'] == 'ext':
        for mastercard in _mastercards:
            app.logger.debug(mastercard)
            if mastercard['type'] > 0:
                c_mastercard = copy.deepcopy(mastercard)
                c_mastercard['cnt'] = 0
                boardcards.append(c_mastercard)
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
                c_mastercard = copy.deepcopy(mastercard)
                c_mastercard['cnt'] = mastercard['stock']
                boardcards.append(c_mastercard)
                # boardcards.append({'name': mastercard['name'], 'cnt': mastercard['stock'], 'cost': mastercard['cost'], 'score': mastercard['score'], 'style': mastercard['style']})

    # initialize for each players
    for player in game['players']:
        player['facilities'] = []
        player['landmarks'] = []

        player['facilities'].append(_mastercards[4])
        player['facilities'].append(_mastercards[5])
        player['facilities'].sort(key=lambda x: (x['score'], x['name']))
        player['coins'] = 3

        for mastercard in _mastercards:
            if mastercard['type'] == 0:
                landmark = copy.deepcopy(mastercard)
                landmark['turn'] = True if game['pack'] == 1 and mastercard['name'] == '役所' else False
                player['landmarks'].append(landmark)

    # game['mastercards'] = _mastercards
    game['stocks'] = stocks
    game['boardcards'] = boardcards
    game['turns'] = game['players']

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

    player['facilities'].sort(key=lambda x: (x['score'], x['name']))
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

    if landmarkid == 0:
        player['dices'] = 2

    if len([landmark for landmark in player['landmarks'] if landmark['turn']]) == len(player['landmarks']):
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
    return json.dumps(dice)


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

    player['facilities'].sort(key=lambda x: (x['score'], x['name']))
    toplayer['facilities'].sort(key=lambda x: (x['score'], x['name']))

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

    player = game['players'][0] # current player
    mycoin = player['coins']
    retCd = ['ok']

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

                if card['name'] == '寿司屋':
                    if len([_landmark for _landmark in _player['landmarks'] if _landmark['turn'] == True and _landmark['name'] == '港']) == 1:
                        diff = diff if player['coins'] > diff else player['coins']
                        player['coins'] -= diff
                        _player['coins'] += diff
                elif card['name'] == '会員制ＢＡＲ':
                    if len([_card for _card in _player['landmarks'] if _card['turn'] == True]) > 2:
                        diff = player['coins']
                        player['coins'] -= diff
                        _player['coins'] += diff
                elif card['name'] == '高級フレンチ':
                    if len([_card for _card in _player['landmarks'] if _card['turn'] == True]) > 1:
                        diff = diff if player['coins'] > diff else player['coins']
                        player['coins'] -= diff
                        _player['coins'] += diff
                else:
                    diff = diff if player['coins'] > diff else player['coins']
                    player['coins'] -= diff
                    _player['coins'] += diff

                results[0] -= diff
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
        elif card['name'] == 'フラワーショップ':
            diff *= len([_card for _card in player['facilities'] if _card['name'] == '花畑'])
            player['coins'] += diff
        elif card['name'] == '食品倉庫':
            diff *= len([_card for _card in player['facilities'] if _card['style'] == '飲食店'])
            player['coins'] += diff
        elif card['name'] == 'ワイナリー':
            # 休業にできないww
            diff *= len([_card for _card in player['facilities'] if _card['name'] == 'ブドウ園'])
            player['coins'] += diff
        elif card['name'] == '引越屋':
            # 検討中
            continue
        elif card['name'] == 'ドリンク工場':
            counts = 0
            for pIdx in game['players']:
                counts += len([_card for _card in player['facilities'] if _card['style'] == '飲食店'])
            diff *= counts
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
            if dice == scores[0]:
                retCd.append('choicePlayer')
        elif card['name'] == 'ビジネスセンター':
            # 効果：（自分のターン）大施設以外の施設１軒を他プレイヤーと交換できる
            diff = 0
            if dice == scores[0]:
                retCd.append('tradeCard')
        elif card['name'] == '雑貨屋':
            if len([_card for _card in player['landmarks'] if _card['turn'] == True]) < 2:
                player['coins'] += diff
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

            if card['name'] == 'サンマ漁船':
                if len([landmark for landmark in _player['landmarks'] if landmark['name'] == '港' and landmark['turn'] == True]) > 0:
                    coins += diff
                    _player['coins'] += diff
            elif card['name'] == 'コーン畑':
                if len([landmark for landmark in _player['landmarks'] if landmark['turn'] == True]) < 2:
                    coins += diff
                    _player['coins'] += diff
            else:
                coins += diff
                _player['coins'] += diff

        results[pIdx] += coins

    game['coin_diff'] = results

    # 街コロ＋（役所効果）
    if game['pack'] == 1 and player['coins'] == 0:
        player['coins'] += 1

    cache.set(gameid, game)
    return json.dumps(retCd)


# next to player
@app.route('/<gameid>/next')
@app.route('/<gameid>/next/<int:nobuy>')
def next_player(gameid, nobuy=0):
    game = cache.get(gameid)

    _player = game['players'][0]

    # 空港の効果
    if game['pack'] == 1:
        if nobuy == 1:
            landmark = [landmark for landmark in _player['landmarks'] if landmark['name'] == '空港'][0]
            if landmark['turn'] == True:
                game['players'][0]['coins'] += 10

    # 遊園地の効果
    if len(game['dice']) > 1:
        if game['dice'][0] == game['dice'][1]:
            landmark = [landmark for landmark in _player['landmarks'] if landmark['name'] == '遊園地'][0]
            if landmark['turn'] == True:
                game['dice'] = []

                cache.set(gameid, game)
                return 'ok'

    game['players'] = np.roll(np.array(game['players']), -1).tolist()
    game['dice'] = []

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
