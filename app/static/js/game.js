document.addEventListener('DOMContentLoaded', function() {
    let ws = null;
    let gameId = null;
    let playerId = null;

    function initializeGame() {
        const gameContainer = document.querySelector('#game-container');
        if (gameContainer) {
            gameId = window.location.pathname.split('/').pop();
            const newPlayerId = gameContainer.getAttribute('data-player-id');
            if (newPlayerId && gameId) {
                playerId = newPlayerId;
                if (!ws || ws.readyState === WebSocket.CLOSED) {
                    connectWebSocket();
                }
            }
        }
    }

    initializeGame();

    // Listen for HTMX events to reinitialize after content swaps
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        initializeGame();
    });

    function connectWebSocket() {
        if (gameId) {
            if (ws) {
                ws.close();
            }
            
            ws = new WebSocket(`ws://${window.location.host}/ws/game/${gameId}`);
            
            ws.onopen = () => {
                // WebSocket connected
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                // For game state changes, fetch fresh content from server
                if (data.type === 'move_made' || data.type === 'game_started' || data.type === 'player_joined' || data.type === 'rematch_started') {
                    fetch(`/api/games/${gameId}`, {
                        headers: {
                            'Accept': 'text/html',
                            'HX-Request': 'true'
                        }
                    })
                    .then(response => response.text())
                    .then(html => {
                        const container = document.getElementById('game-container');
                        if (container) {
                            // Create a temporary container to parse the HTML
                            const tempDiv = document.createElement('div');
                            tempDiv.innerHTML = html;
                            const newContainer = tempDiv.firstElementChild;
                            
                            // Replace the container
                            container.parentNode.replaceChild(newContainer, container);
                            
                            // Process the new content with HTMX
                            if (typeof htmx !== 'undefined') {
                                htmx.process(newContainer);
                            }
                            initializeGame();
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching updated game state:', error);
                    });
                }
            };

            ws.onclose = () => {
                setTimeout(connectWebSocket, 1000);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }
    }
});