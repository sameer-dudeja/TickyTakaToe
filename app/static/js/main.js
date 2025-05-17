// WebSocket connection
function connectWebSocket(gameId) {
    const ws = new WebSocket(`ws://${window.location.host}/ws/game/${gameId}`);
    
    ws.onmessage = async function(event) {
        const data = JSON.parse(event.data);
        
        // For all game state changes, fetch the latest game state
        if (['player_joined', 'game_started', 'move_made'].includes(data.type)) {
            const response = await fetch(`/api/games/${gameId}`, {
                headers: {
                    'Accept': 'text/html',
                    'HX-Request': 'true'
                }
            });
            if (response.ok) {
                const container = document.getElementById('game-container');
                container.innerHTML = await response.text();
            }
        }
    };

    ws.onclose = function() {
        // Try to reconnect every 1 second
        setTimeout(() => connectWebSocket(gameId), 1000);
    };
}

// Initialize WebSocket if we're on a game page
const gameId = document.querySelector('meta[name="game-id"]')?.content;
if (gameId) {
    connectWebSocket(gameId);
} 