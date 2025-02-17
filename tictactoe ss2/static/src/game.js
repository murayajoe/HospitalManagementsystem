odoo.define('tic_tac_toe.game', function(require) {
    var ajax = require('web.ajax');

    function startNewGame() {
        ajax.jsonRpc('/tic_tac_toe/new_game', 'call', {}).then(function(data) {
            updateBoard(data.board);
            document.getElementById("currentPlayer").innerText = data.current_player;
        });
    }

    function makeMove(position) {
        ajax.jsonRpc('/tic_tac_toe/move', 'call', {game_id: 1, position: position}).then(function(data) {
            updateBoard(data.board);
            document.getElementById("currentPlayer").innerText = data.current_player;
            if (data.winner) alert("Winner: " + data.winner);
        });
    }

    function updateBoard(board) {
        let boardDiv = document.getElementById("gameBoard");
        boardDiv.innerHTML = "";
        board.split("").forEach((cell, index) => {
            let btn = document.createElement("button");
            btn.innerText = cell === '-' ? '' : cell;
            btn.onclick = () => makeMove(index);
            boardDiv.appendChild(btn);
        });
    }
});
