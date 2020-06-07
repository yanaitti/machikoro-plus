import os
import unittest
import tempfile
import main
import json
import collections
import random

class MainTestCase(unittest.TestCase):

    def setUp(self):
        main.app.config['TESTING'] = True
        self.app = main.app.test_client()

    def create_game(self):
        return self.app.get('/create', follow_redirects=True)

    def join_game(self, gameid):
        return self.app.get(gameid + '/join', follow_redirects=True)

    def join_game_w_name(self, gameid, nickname):
        return self.app.get(gameid + '/join/' + nickname, follow_redirects=True)

    def start_game(self, gameid, ext):
        if ext != '':
            return self.app.get(gameid + '/start/ext', follow_redirects=True)
        else:
            return self.app.get(gameid + '/start', follow_redirects=True)

    def status_game(self, gameid):
        return self.app.get(gameid + '/status', follow_redirects=True)

    def roll_dice(self, gameid, rollcnt):
        return self.app.get(gameid + '/roll/' + str(rollcnt), follow_redirects=True)

    def judgement_dice(self, gameid, dice):
        return self.app.get(gameid + '/judgement/' + str(dice), follow_redirects=True)

    def buying_landmark(self, gameid, playerid, landmarkid):
        return self.app.get(gameid + '/' + playerid + '/buy/landmark/' + str(landmarkid), follow_redirects=True)

    def buying_facility(self, gameid, playerid, facilityid):
        return self.app.get(gameid + '/' + playerid + '/buy/facility/' + str(facilityid), follow_redirects=True)

    def next_game(self, gameid):
        return self.app.get(gameid + '/next', follow_redirects=True)

    def trun_status(self, game_status, turnno):
        print('####################################################')
        print ('turn ' + str(turnno))
        print('####################################################')
        for boardcard in game_status['boardcards']:
            print(boardcard['name'] + ':' + str(boardcard['cnt']))
        print('##---------------------------------##')
        for facility in game_status['players'][0]['facilities']:
            print(facility['name'])
        print('##---------------------------------##')
        for landmark in game_status['players'][0]['landmarks']:
            print(landmark['name'] + ':' + str(landmark['turn']))
        print('##---------------------------------##')
        for pIdx, player in enumerate(game_status['players']):
            print(str(pIdx + 1) + ':' + str(player['coins']))
        print('##---------------------------------##')


    def test_all_scenario(self):
        random.seed(1)

        players = []

        ###########################################################
        # Create Game
        rv = self.create_game()
        assert '' != rv.get_data()
        gameid = str(rv.get_data().decode())
        # print(gameid)
        players.append(gameid)

        ###########################################################
        # Join Game
        for i in range(2):
            if i == 1:
                rv = self.join_game_w_name(gameid, '太郎')
                data = json.loads(rv.get_data())
                assert data['nickname'] != data['playerid'] and data['nickname'] == '太郎'
            else:
                rv = self.join_game(gameid)
                data = json.loads(rv.get_data())
                assert data['nickname'] == data['playerid']

        ###########################################################
        # Start Game
        print('#####################################')

        rv = self.start_game(gameid, '')
        assert b'ok' in rv.get_data()

        ###########################################################
        # Status Game
        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        boardcards = [boardcard['cnt'] for boardcard in game_status['boardcards'] if boardcard['cnt'] > 0]

        for boardcard in game_status['boardcards']:
            print(boardcard['name'] + ':' + str(boardcard['cnt']))

        ###########################################################
        # Start Game
        print('#####################################')

        rv = self.start_game(gameid, 'ext')
        assert b'ok' in rv.get_data()

        ###########################################################
        # Status Game
        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        boardcards = [boardcard['cnt'] for boardcard in game_status['boardcards'] if boardcard['cnt'] > 0]

        assert 'started' == game_status['status']
        # player数チェック
        assert 3 == len(game_status['players'])
        # 全体のカード数チェック
        assert 84 == (len(game_status['stocks']) + sum(boardcards))
        for player in game_status['players']:
            assert 2 == len(player['facilities'])
            assert 3 == player['coins']
            assert 4 == len(player['landmarks'])
            for landmark in player['landmarks']:
                assert False == landmark['turn']

        assert gameid == game_status['players'][0]['playerid']

        for boardcard in game_status['boardcards']:
            print(boardcard['name'] + ':' + str(boardcard['cnt']))

        # ####################################################
        self.trun_status(game_status, 1)
        # ####################################################

        ###########################################################
        # ダイスを振る(1個)
        rv = self.roll_dice(gameid, 1)
        dice = json.loads(rv.get_data(as_text=True))

        assert dice[0] in range(1, 6)
        assert 1 == len(dice)

        # ダイスを振る(2個)
        rv = self.roll_dice(gameid, 2)
        dice = json.loads(rv.get_data(as_text=True))

        print(dice)
        assert dice[0] in range(1, 7)
        assert dice[1] in range(1, 7)
        assert 2 == len(dice)

        ###########################################################
        # カードの効果を得る
        # （誰のターンでも）1コイン受け取る
        rv = self.judgement_dice(gameid, 1)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        for player in game_status['players']:
            assert 4 == int(player['coins'])

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 駅＜ランドマーク＞を買う

        # NG - no stock
        rv = self.buying_facility(gameid, game_status['players'][0]['playerid'], 2)
        assert b'ng' in rv.get_data()

        # NG - no money
        rv = self.buying_facility(gameid, game_status['players'][0]['playerid'], 12)
        assert b'ng' in rv.get_data()

        # OK
        rv = self.buying_landmark(gameid, game_status['players'][0]['playerid'], 0)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # Player 1 は駅を買ってダイスが増えた
        assert 0 == int(game_status['players'][0]['coins'])
        assert True == game_status['players'][0]['landmarks'][0]['turn']

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # 入れ替わったことのチェック
        assert gameid != game_status['players'][0]['playerid']
        assert gameid == game_status['players'][-1]['playerid']

        # ####################################################
        self.trun_status(game_status, 2)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        # 効果なし
        rv = self.judgement_dice(gameid, 6)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        assert 4 == int(game_status['players'][0]['coins'])
        assert 4 == int(game_status['players'][1]['coins'])
        assert 0 == int(game_status['players'][2]['coins'])

        ###########################################################
        # 施設またはランドマークの建設を行う
        # コンビニ＜施設＞を買う
        rv = self.buying_facility(gameid, game_status['players'][0]['playerid'], 4)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # Player 2 はコンビニを買ってカードが増えた
        assert 2 == int(game_status['players'][0]['coins'])
        assert 3 == len(game_status['players'][0]['facilities'])
        assert 0 == game_status['boardcards'][4]['cnt']

        print('#####################################')
        for boardcard in game_status['boardcards']:
            print(boardcard['name'] + ':' + str(boardcard['cnt']))

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # 入れ替わったことのチェック
        assert gameid != game_status['players'][0]['playerid']
        assert gameid == game_status['players'][-2]['playerid']

        # ####################################################
        self.trun_status(game_status, 3)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        # （他人のターン）目を出した人から１コインもらう
        rv = self.judgement_dice(gameid, 3)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        assert 4 == int(game_status['players'][0]['coins']) # player 3
        assert 0 == int(game_status['players'][1]['coins']) # player 1
        assert 2 == int(game_status['players'][2]['coins']) # player 2

        ###########################################################
        # 施設またはランドマークの建設を行う
        # ファミレス＜施設＞を買う
        rv = self.buying_facility(gameid, game_status['players'][0]['playerid'], 9)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # Player 3 はファミレスを買ってカードが増えた
        assert 1 == int(game_status['players'][0]['coins'])
        assert 3 == len(game_status['players'][0]['facilities'])
        assert 1 == game_status['boardcards'][9]['cnt']

        print('#####################################')
        for boardcard in game_status['boardcards']:
            print(boardcard['name'] + ':' + str(boardcard['cnt']))

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # 入れ替わったことのチェック
        assert gameid == game_status['players'][0]['playerid']

        # ####################################################
        self.trun_status(game_status, 4)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        # （他人のターン）目を出した人から2コインもらう
        rv = self.judgement_dice(gameid, 10)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # player 3へ2コインとられるはずが、0なので、とられない
        assert 0 == int(game_status['players'][0]['coins']) # player 1
        assert 2 == int(game_status['players'][1]['coins']) # player 2
        # player 1ヵら2コインもらうはずが、0なので、もらえない
        assert 1 == int(game_status['players'][2]['coins']) # player 3

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 0コインなので何もできない

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # 入れ替わったことのチェック
        assert gameid != game_status['players'][0]['playerid']
        assert gameid == game_status['players'][-1]['playerid']

        # ####################################################
        self.trun_status(game_status, 5)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        # （自分のターン）銀行から３コインもらう
        rv = self.judgement_dice(gameid, 4)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # 銀行から3コインもらう
        assert 5 == int(game_status['players'][0]['coins']) # player 2
        assert 1 == int(game_status['players'][1]['coins']) # player 3
        assert 0 == int(game_status['players'][2]['coins']) # player 1

        ###########################################################
        # 施設またはランドマークの建設を行う
        # チーズ工場＜施設＞を買う
        rv = self.buying_facility(gameid, game_status['players'][0]['playerid'], 6)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # Player 2 はチーズ工場を買ってカードが増えた
        assert 0 == int(game_status['players'][0]['coins'])
        assert 4 == len(game_status['players'][0]['facilities'])
        assert 1 == game_status['boardcards'][6]['cnt']

        print('#####################################')
        for boardcard in game_status['boardcards']:
            print(boardcard['name'] + ':' + str(boardcard['cnt']))

        print('##-----------------------------------')
        for facility in game_status['players'][0]['facilities']:
            print(facility['name'])

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # 入れ替わったことのチェック
        assert gameid != game_status['players'][0]['playerid']
        assert gameid == game_status['players'][-2]['playerid']

        # ####################################################
        self.trun_status(game_status, 6)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        # （誰のターンでも）銀行から１コインもらう
        #
        rv = self.judgement_dice(gameid, 2)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # 全員が銀行から1コインもらう
        assert 2 == int(game_status['players'][0]['coins']) # player 3
        assert 1 == int(game_status['players'][1]['coins']) # player 1
        assert 1 == int(game_status['players'][2]['coins']) # player 2

        ###########################################################
        # 施設またはランドマークの建設を行う
        # カフェ＜施設＞を買う
        rv = self.buying_facility(gameid, game_status['players'][0]['playerid'], 3)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # Player 2 はカフェを買ってカードが増えた
        assert 0 == int(game_status['players'][0]['coins'])
        assert 4 == len(game_status['players'][0]['facilities'])
        assert 1 == game_status['boardcards'][1]['cnt']

        print('#####################################')
        for boardcard in game_status['boardcards']:
            print(boardcard['name'] + ':' + str(boardcard['cnt']))

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # 入れ替わったことのチェック
        assert gameid == game_status['players'][0]['playerid']

        # ####################################################
        self.trun_status(game_status, 7)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        # （誰のターンでも）銀行から１コインもらう
        #
        rv = self.judgement_dice(gameid, 1)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # 全員が銀行から1コインもらう
        assert 2 == int(game_status['players'][0]['coins']) # player 1
        assert 2 == int(game_status['players'][1]['coins']) # player 2
        assert 1 == int(game_status['players'][2]['coins']) # player 3

        ###########################################################
        # 施設またはランドマークの建設を行う
        # カフェ＜施設＞を買う
        rv = self.buying_facility(gameid, game_status['players'][0]['playerid'], 3)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # Player 1 はカフェを買ってカードが増えた
        assert 0 == int(game_status['players'][0]['coins'])
        assert 3 == len(game_status['players'][0]['facilities'])
        assert 0 == game_status['boardcards'][3]['cnt']

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 8)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 7)
        print(rv.get_data().decode())
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （自分のターン）銀行から自分の【牧場】１軒につき３コインもらう
        assert 5 == int(game_status['players'][0]['coins']) # player 2
        assert 1 == int(game_status['players'][1]['coins']) # player 3
        assert 0 == int(game_status['players'][2]['coins']) # player 1

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 購入しない

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 9)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        # （誰のターンでも）銀行から１コインもらう
        #
        rv = self.judgement_dice(gameid, 2)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # 全員が銀行から1コインもらう
        assert 2 == int(game_status['players'][0]['coins']) # player 3
        assert 1 == int(game_status['players'][1]['coins']) # player 1
        assert 6 == int(game_status['players'][2]['coins']) # player 2

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 購入しない

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 10)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 9)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （他人のターン）目を出した人から２コインもらう
        assert 0 == int(game_status['players'][0]['coins']) # player 1
        assert 6 == int(game_status['players'][1]['coins']) # player 2
        assert 3 == int(game_status['players'][2]['coins']) # player 3

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 購入しない

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 11)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 4)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （自分のターン）銀行から３コインもらう
        assert 9 == int(game_status['players'][0]['coins']) # player 2
        assert 3 == int(game_status['players'][1]['coins']) # player 3
        assert 0 == int(game_status['players'][2]['coins']) # player 1

        ###########################################################
        # 施設またはランドマークの建設を行う
        # ファミレス＜施設＞を買う
        rv = self.buying_facility(gameid, game_status['players'][0]['playerid'], 9)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        assert 6 == int(game_status['players'][0]['coins'])
        assert 5 == len(game_status['players'][0]['facilities'])
        assert 0 == game_status['boardcards'][9]['cnt']

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 12)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 9)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （他人のターン）目を出した人から２コインもらう
        assert 1 == int(game_status['players'][0]['coins']) # player 3
        assert 0 == int(game_status['players'][1]['coins']) # player 1
        assert 8 == int(game_status['players'][2]['coins']) # player 2

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 購入しない

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 13)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 1)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （誰のターンでも）銀行から１コインもらう
        assert 1 == int(game_status['players'][0]['coins']) # player 1
        assert 9 == int(game_status['players'][1]['coins']) # player 2
        assert 2 == int(game_status['players'][2]['coins']) # player 3

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 購入しない

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 14)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 4)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （自分のターン）銀行から３コインもらう
        assert 12 == int(game_status['players'][0]['coins']) # player 3
        assert 2 == int(game_status['players'][1]['coins']) # player 1
        assert 1 == int(game_status['players'][2]['coins']) # player 2

        ###########################################################
        # 施設またはランドマークの建設を行う
        # ショッピングモール＜ランドマーク＞
        rv = self.buying_landmark(gameid, game_status['players'][0]['playerid'], 1)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        assert 2 == int(game_status['players'][0]['coins'])
        assert 5 == len(game_status['players'][0]['facilities'])
        assert True == game_status['players'][0]['landmarks'][1]['turn']

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 15)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 10)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （他人のターン）目を出した人から２コインもらう
        assert 0 == int(game_status['players'][0]['coins']) # player 1
        assert 1 == int(game_status['players'][1]['coins']) # player 2
        assert 4 == int(game_status['players'][2]['coins']) # player 3

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 購入しない

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 16)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 1)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （誰のターンでも）銀行から１コインもらう
        assert 2 == int(game_status['players'][0]['coins']) # player 2
        assert 5 == int(game_status['players'][1]['coins']) # player 3
        assert 1 == int(game_status['players'][2]['coins']) # player 1

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 購入しない

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 17)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 7)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （自分のターン）銀行から自分の【牧場】１軒につき３コインもらう
        assert 8 == int(game_status['players'][0]['coins']) # player 3
        assert 1 == int(game_status['players'][1]['coins']) # player 1
        assert 2 == int(game_status['players'][2]['coins']) # player 2

        ###########################################################
        # 施設またはランドマークの建設を行う
        # スタジアム＜施設＞を買う
        rv = self.buying_facility(gameid, game_status['players'][0]['playerid'], 12)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        assert 2 == int(game_status['players'][0]['coins'])
        assert 6 == len(game_status['players'][0]['facilities'])

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 18)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 1)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （誰のターンでも）銀行から１コインもらう
        assert 2 == int(game_status['players'][0]['coins']) # player 1
        assert 3 == int(game_status['players'][1]['coins']) # player 2
        assert 3 == int(game_status['players'][2]['coins']) # player 3

        ###########################################################
        # 施設またはランドマークの建設を行う
        # パン屋＜施設＞を買う
        rv = self.buying_facility(gameid, game_status['players'][0]['playerid'], 2)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        assert 1 == int(game_status['players'][0]['coins'])
        assert 5 == len(game_status['players'][0]['facilities'])

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 19)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 1)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （誰のターンでも）銀行から１コインもらう
        assert 4 == int(game_status['players'][0]['coins']) # player 2
        assert 4 == int(game_status['players'][1]['coins']) # player 3
        assert 2 == int(game_status['players'][2]['coins']) # player 1

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 購入しない

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # ####################################################
        self.trun_status(game_status, 20)
        # ####################################################

        ###########################################################
        # カードの効果を得る
        #
        rv = self.judgement_dice(gameid, 6)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())

        # （自分のターン）全員から２コインもらう
        assert 8 == int(game_status['players'][0]['coins']) # player 3
        assert 0 == int(game_status['players'][1]['coins']) # player 1
        assert 2 == int(game_status['players'][2]['coins']) # player 2

        ###########################################################
        # 施設またはランドマークの建設を行う
        # 購入しない

        ###########################################################
        # 次の人へ
        rv = self.next_game(gameid)
        assert b'ok' in rv.get_data()

        rv = self.status_game(gameid)
        game_status = json.loads(rv.get_data())


if __name__ == '__main__':
    unittest.main()
