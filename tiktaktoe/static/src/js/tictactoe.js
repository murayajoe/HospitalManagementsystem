odoo.define('tic_tac_toe.tictactoe', function (require) {
    "use strict";

    var core = require('web.core');
    var rpc = require('web.rpc');

    $(document).on('click', '.tictactoe-cell', function () {
        var cell = $(this);
        var game_id = cell.data('game-id');
        var position = cell.data('position');
        var player = $('#current-player').val();

        rpc.query({
            route: '/tic_tac_toe/move',
            params: { game_id: game_id, position: position, player: player }
        }).then(function (result) {
            if (result.error) {
                alert(result.error);
            } else {
                cell.text(player);
                if (result.winner) {
                    alert("Winner: " + result.winner);
                }
            }
        });
    });
});
