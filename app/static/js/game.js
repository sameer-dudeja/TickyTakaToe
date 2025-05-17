document.addEventListener('DOMContentLoaded', function() {
    let ws = null;
    let gameId = null;
    let playerId = null;

    function initializeGame() {
        const gameContainer = document.querySelector('#game-container');
        if (gameContainer) {
            gameId = window.location.pathname.split('/').pop();
            const newPlayerId = gameContainer.getAttribute('data-player-id');
            if (newPlayerId) {
                playerId = newPlayerId;
                connectWebSocket();
            }
        }
    }

    initializeGame();

    document.body.addEventListener('htmx:afterSwap', function(evt) {
        const gameContainer = document.querySelector('#game-container');
        if (gameContainer) {
            const newPlayerId = gameContainer.getAttribute('data-player-id');
            if (newPlayerId) {
                playerId = newPlayerId;
            }
        }
        initializeGame();
    });

    function connectWebSocket() {
        if (gameId) {
            ws = new WebSocket(`ws://${window.location.host}/ws/game/${gameId}`);
            
            ws.onopen = () => {
                fetch(`/api/games/${gameId}`)
                    .then(response => response.json())
                    .then(data => {
                        const container = document.querySelector('#game-container');
                        if (container && !playerId) {
                            playerId = container.getAttribute('data-player-id');
                        }
                        updateGameState(data);
                    });
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (!playerId) {
                    const gameContainer = document.querySelector('#game-container');
                    if (gameContainer) {
                        playerId = gameContainer.getAttribute('data-player-id');
                    }
                }
                
                if (data.type === 'move_made' || data.type === 'game_started') {
                    updateGameState(data);
                }
            };

            ws.onclose = () => {
                setTimeout(connectWebSocket, 1000);
            };
        }
    }

    function updateGameState(gameState) {
        const board = gameState.board;
        const cells = document.querySelectorAll('.game-board button');
        const isCurrentPlayer = gameState.current_player === playerId;
        const isGameInProgress = gameState.game_status === 'in_progress';
        
        cells.forEach((cell, index) => {
            const row = Math.floor(index / board.length);
            const col = index % board.length;
            const value = board[row][col];
            
            cell.textContent = value || '';
            
            if (value && !cell.classList.contains('game-move')) {
                cell.classList.add('game-move');
            }
            
            const isOccupied = value !== null;
            const canMove = isGameInProgress && isCurrentPlayer && !isOccupied;
            
            cell.disabled = !canMove;
            cell.classList.toggle('cursor-not-allowed', !canMove);
            cell.classList.toggle('cursor-pointer', canMove);
            cell.classList.toggle('opacity-75', !canMove);
            cell.classList.toggle('hover:bg-gray-200', canMove);
            cell.classList.toggle('active:bg-gray-300', canMove);

            if (canMove) {
                cell.setAttribute('hx-post', `/api/games/${gameId}/move`);
                cell.setAttribute('hx-vals', JSON.stringify({
                    row: row,
                    col: col,
                    player_id: playerId
                }));
                cell.setAttribute('hx-target', '#game-container');
                cell.setAttribute('hx-swap', 'outerHTML');
            } else {
                cell.removeAttribute('hx-post');
                cell.removeAttribute('hx-vals');
            }
        });

        const statusElement = document.querySelector('#turn-status');
        if (statusElement && gameState.players) {
            if (gameState.game_status === 'finished') {
                if (gameState.winner === playerId) {
                    statusElement.textContent = 'You won!';
                    statusElement.classList.remove('text-blue-600', 'text-red-600');
                    statusElement.classList.add('text-green-600', 'winner');
                } else if (gameState.winner) {
                    const winnerName = gameState.players.find(p => p.id === gameState.winner)?.name || 'Opponent';
                    statusElement.textContent = `${winnerName} won!`;
                    statusElement.classList.remove('text-blue-600', 'text-green-600');
                    statusElement.classList.add('text-red-600');
                } else {
                    statusElement.textContent = "It's a draw!";
                    statusElement.classList.remove('text-blue-600', 'text-green-600', 'text-red-600');
                    statusElement.classList.add('text-gray-600');
                }
            } else if (isCurrentPlayer) {
                statusElement.textContent = 'Your turn!';
                statusElement.classList.remove('text-red-600', 'text-green-600');
                statusElement.classList.add('text-blue-600');
            } else {
                const currentPlayerName = gameState.players.find(p => p.id === gameState.current_player)?.name || 'Opponent';
                statusElement.textContent = `Waiting for ${currentPlayerName} to move...`;
                statusElement.classList.remove('text-blue-600', 'text-green-600');
                statusElement.classList.add('text-red-600');
            }
        }
    }
}); 