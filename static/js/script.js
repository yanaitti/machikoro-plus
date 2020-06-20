var timeout = 1000;
var timer = '';

$(function() {
  var gId = '';
  var cId = '';

  // Create Game
  $('#createGame').click(function() {
    $('#message').empty();
    $.ajax('create' + '/' + $('#cName_inp').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#createGame').prop("disabled", true);
      $('#joinGame').prop("disabled", true);
      $('#gId').text(data);
      $('#cId').text(data);
      $('#cName').text($('#cName_inp').val());
      $('#gStatus').text('waiting');
      gId = data;
      cId = data;
      $('#sec1').show();
      timer = setTimeout(status_check(gId, cId), timeout)
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // Join Game
  $('#joinGame').click(function() {
    $('#message').empty();
    $.ajax($('#gId_inp').val() + '/join/' + $('#cName_inp').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#createGame').prop("disabled", true);
      $('#joinGame').prop("disabled", true);
      _tmp = data.split(' ,');
      $('#cId').text(_tmp[0]);
      $('#cName').text(_tmp[1]);
      $('#gStatus').text(_tmp[2]);
      gId = $('#gId_inp').val();
      cId = _tmp[0];
      timer = setTimeout(status_check(gId, cId), timeout)
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // <通常ルール>
  $('#startGame1').click(function() {
    $('#message').empty();
    $.ajax(gId + '/start',
      {
        type: 'get',
      }
    )
    .done(function(data) {
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // <拡張ルール>
  $('#startGame2').click(function() {
    $('#message').empty();
    $.ajax(gId + '/start/ext',
      {
        type: 'get',
      }
    )
    .done(function(data) {
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // 街コロの有効カード取得
  $('#getAvailableCards1').click(function() {
    $('#message').empty();
    $.getJSON(gId + '/availablelists/0',
      {
        type: 'get',
      }
    )
    .done(function(data) {
      // console.log(data);
      $('#availableCardList').empty();
      for(var mIdx in data){
        if(data[mIdx].available){
          $('#availableCardList').append('<input type="checkbox" name="cards[]" value="'+mIdx+'" checked>'+data[mIdx].name+'<br/>');
        }else{
          $('#availableCardList').append('<input type="checkbox" name="cards[]" value="'+mIdx+'" disabled>'+data[mIdx].name+'<br/>');
        }
      }
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // 街コロ＋の有効カード取得
  $('#getAvailableCards2').click(function() {
    $('#message').empty();
    $.getJSON(gId + '/availablelists/1',
      {
        type: 'get',
      }
    )
    .done(function(data) {
      // console.log(data);
      $('#availableCardList').empty();
      for(var mIdx in data){
        if(data[mIdx].available){
          $('#availableCardList').append('<input type="checkbox" name="cards[]" value="'+mIdx+'" checked>'+data[mIdx].name+'<br/>');
        }else{
          $('#availableCardList').append('<input type="checkbox" name="cards[]" value="'+mIdx+'" disabled>'+data[mIdx].name+'<br/>');
        }
      }
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // 使用カードを設定
  $('#setGameCards').click(function() {
    $('#message').empty();
    var selCards = [];
    $('input[name="cards[]"]:checked').each(function(){selCards.push($(this).val());});
    console.log(selCards);
    $.getJSON(gId + '/setup/' + selCards,
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#availableCardList').empty();
      $('#setGameCards').prop('disabled', true);
      $('#getAvailableCards1').prop('disabled', true);
      $('#getAvailableCards2').prop('disabled', true);
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // 施設の購入
  $('#buy_facility').click(function() {
    $('#message').empty();
    $.ajax(gId + '/' + cId + '/buy/facility/' + $('#sel_buy_facility').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#buy_landmark').prop("disabled", true);
      $('#buy_facility').prop("disabled", true);
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // ランドマークの購入
  $('#buy_landmark').click(function() {
    $('#message').empty();
    $.ajax(gId + '/' + cId + '/buy/landmark/' + $('#sel_buy_landmark').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#buy_landmark').prop("disabled", true);
      $('#buy_facility').prop("disabled", true);
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // roll the dice
  $('#roll_dice').click(function() {
    $('#message').empty();
    $.getJSON(gId + '/roll/' + $('input[name="choice_dice"]:checked').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#hide_dice').val('0');
      for(dIdx in data){
        $('#hide_dice').val(Number($('#hide_dice').val()) + Number(data[dIdx]));
      }
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // judgement
  $('#judgement').click(function() {
    $('#message').empty();
    $.getJSON(gId + '/judgement/' + $('#hide_dice').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#judgement').prop("disabled", true);
      // alert($.inArray('ok', data));
      if($.inArray('choicePlayer', data) > 0){
        $('#sec5').show();
      }
      if($.inArray('tradeCard', data) > 0){
        $('#sec4').show();
      }
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // trade_card
  $('#trade_card').click(function() {
    $('#message').empty();
    $.ajax(gId + '/' + cId + '/trade/' + $('#sel_player2').val() + '/' + $('#sel_card1').val() + '/' + $('#sel_card2').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#sec4').hide();
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // get_point
  $('#get_point').click(function() {
    $('#message').empty();
    $.ajax(gId + '/' + cId + '/choice/' + $('#sel_player2').val(),
      {
        type: 'get',
      }
    )
    .done(function(data) {
      $('#sec5').hide();
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });

  // plus2
  $('#plus2').click(function() {
    $('#hide_dice').val(Number($('#hide_dice').val()) + 2);
    $('#plus2').prop('disabled', true);
    // 一度disableにしてるけど、メインルーチンの判定で無効にされている。考える、、、
  });

  // Next player
  $('#next_player').click(function() {
    $('#message').empty();
    var path = gId + '/next'
    if(!$('#buy_landmark').prop('disabled') && !$('#buy_facility').prop('disabled')){
      path = path + '/1'
    }
    $.ajax(path,
      {
        type: 'get',
      }
    )
    .done(function(data) {
      // console.log(data)
      $('#buy_facility').prop("disabled", false);
      $('#buy_landmark').prop("disabled", false);
      $('#roll_dice').prop("disabled", false);
      $('#judgement').prop("disabled", false);
      $('#message').text('次に移動しました');
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
  });
});

var status_check = function(gId, cId){
  setTimeout(function(){
    $('#message').empty();
    // all status
    $.getJSON(gId + '/status',
      {
        type: 'get',
      }
    )
    .done(function(data) {
      console.log(data)
      $('#gStatus').text(data.status);
      playerPos = 0;
      teamid = 0;

      // Applying List
      $('#applyingList').empty();
      for(var pIdx in data.players){
        // console.log(data.players[pIdx])
        $('#applyingList').append(data.players[pIdx].nickname + '(' + data.players[pIdx].playerid + ')' + ',');
        if(cId == data.players[pIdx].playerid){
          playerPos = pIdx;
        }
      }

      switch(data.status){
        case 'started':
          $('#sec2').show();

          if(data.players[0].playerid == cId){
            $('#sec3').show();
          }else{
            $('#sec3').hide();
            $('#sec4').hide();
            $('#sec5').hide();
          }

          console.log('cId:' + cId)

          $('#playerinformation').empty();
          for(var pIdx in data.turns){
            _player = data.turns[pIdx];

            var rowtable = $('<tr></tr>').appendTo($('#playerinformation'));
            $('<td colspan="2"> Name:' + _player.nickname + ' / Coin:' + _player.coins + '</td>').appendTo(rowtable);

            // landmarks
            var rowtable = $('<tr></tr>').appendTo($('#playerinformation'));
            var coltable = $('<td></td>').appendTo(rowtable);
            var rowul = $('<ul class="nav"></ul>').appendTo(coltable);
            for(var pIdx in _player.landmarks){
              landmark = _player.landmarks[pIdx]
              $('<li>' + landmark.name + '<br/>=' + landmark.cost + '=<br/>&lt;' + (landmark.turn == true? '建設済み':'工事中') + '&gt;</li>').appendTo(rowul);
              // $('<li></li>').appendTo(rowul);
            }

            // facilities
            var rowtable = $('<tr></tr>').appendTo($('#playerinformation'));
            var coltable = $('<td></td>').appendTo(rowtable);
            var rowul = $('<ul class="nav"></ul>').appendTo(coltable);
            for(var fIdx in _player.facilities){
              facility = _player.facilities[fIdx]
              switch(facility.type){
                case 1:
                  // green
                  $('<li><font color="#00b300">■</font>(' + facility.score + ')<br/>' + facility.name + '</li>').appendTo(rowul);
                  break;
                case 2:
                  // red
                  $('<li><font color="#b30000">▲</font>(' + facility.score + ')<br/>' + facility.name + '</li>').appendTo(rowul);
                  break;
                case 3:
                  // blue
                  $('<li><font color="#0077b3">●</font>(' + facility.score + ')<br/>' + facility.name + '</li>').appendTo(rowul);
                  break;
              }
            }
          }

          var gCnt = 0;

          $('#boardcards').empty();
          for(var gIdx in data.boardcards){
            if(gCnt % 5 == 0){
              var rowtable = $('<tr></tr>').appendTo($('#boardcards'));
            }
            if(data.boardcards[gIdx].cnt > 0){
              switch(data.boardcards[gIdx].type){
                case 1:
                  // green
                  $('<td align="center"><font color="#00b300">■</font>(' + data.boardcards[gIdx].score + ')<br/>' + data.boardcards[gIdx].name + '<br/>=' + data.boardcards[gIdx].cost + '=<br/>&lt;' + data.boardcards[gIdx].cnt + '&gt;</td>').appendTo(rowtable);
                  break;
                case 2:
                  // red
                  $('<td align="center"><font color="#b30000">▲</font>(' + data.boardcards[gIdx].score + ')<br/>' + data.boardcards[gIdx].name + '<br/>=' + data.boardcards[gIdx].cost + '=<br/>&lt;' + data.boardcards[gIdx].cnt + '&gt;</td>').appendTo(rowtable);
                  break;
                case 3:
                  // blue
                  $('<td align="center"><font color="#0077b3">●</font>(' + data.boardcards[gIdx].score + ')<br/>' + data.boardcards[gIdx].name + '<br/>=' + data.boardcards[gIdx].cost + '=<br/>&lt;' + data.boardcards[gIdx].cnt + '&gt;</td>').appendTo(rowtable);
                  break;
              }
              gCnt++;
            }
          }
          if(data.boardcards.length != $('#sel_buy_facility').children('option').length){
            $('#sel_buy_facility').children().remove();
            for(var gIdx in data.boardcards){
              $('#sel_buy_facility').append('<option value="'+gIdx+'">' + data.boardcards[gIdx].name + '</option>');
            }
            $('#sel_card1').children().remove();
            $('#sel_card2').children().remove();
            for(var gIdx in data.boardcards){
              if(data.boardcards[gIdx].style != 'ランドマーク'){
                $('#sel_card1').append('<option value="'+gIdx+'">' + data.boardcards[gIdx].name + '</option>');
                $('#sel_card2').append('<option value="'+gIdx+'">' + data.boardcards[gIdx].name + '</option>');
              }
            }
          }

          if(_player.landmarks.length != $('#sel_buy_landmark').children('option').length){
            $('#sel_buy_landmark').children().remove();
            for(var pIdx in _player.landmarks){
              landmark = _player.landmarks[pIdx]
              $('#sel_buy_landmark').append('<option value="'+pIdx+'">' + landmark.name + '</option>');
            }
          }

          $('#dice').text(data.dice.join(','));
          $('#yourdice').text(data.dice.join(','));
          if(data.players[playerPos].dices == 2){
            $('input[type="radio"]').prop("disabled", false);
          }

          if(data.players.length != $('#sel_player1').children('option').length){
            $('#sel_player1').children().remove();
            $('#sel_player2').children().remove();
            for(var pIdx in data.players){
              if(pIdx != playerPos){
                $('#sel_player1').append('<option value="'+data.players[pIdx].playerid+'">'+data.players[pIdx].nickname+'</option>');
                $('#sel_player2').append('<option value="'+data.players[pIdx].playerid+'">'+data.players[pIdx].nickname+'</option>');
              }
            }
          }
          if((Number($('#hide_dice').val()) > 10)&&(data.pack == 1)){
            if(data.players[playerPos].landmarks[5].turn == true){
              $('#plus2').prop("disabled", false);
            }
          }

          break;
        case 'end':
          $('#gameover').text('Game Over');
          $('input[type="radio"]').prop("disabled", false);
          $('#setteam').prop("disabled", false);
          $('#sec4').css('display', 'none');
          $('#card_sel').children().remove();
          break;
      }
    })
    .fail(function() {
      $('#message').text('エラーが発生しました');
    });
    timer = setTimeout(status_check(gId, cId), timeout)
  }, timeout);
}
