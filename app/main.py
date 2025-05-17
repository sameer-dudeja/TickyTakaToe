from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Query, Response, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from typing import Dict, Set, Optional
from .api import game

app = FastAPI(title="TickyTakaToe")

# Add session middleware with a secure secret key
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secure-key-here",  # In production, use a proper secure key
    session_cookie="ticky_session",
    max_age=3600,  # 1 hour in seconds
    same_site='lax',  # Allow session to work with redirects
    https_only=False  # Since we're running on localhost
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Share templates with the game router
game.templates = templates

# Include game router
app.include_router(game.router, prefix="/api")

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.game_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str):
        await websocket.accept()
        if game_id not in self.game_connections:
            self.game_connections[game_id] = set()
        self.game_connections[game_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, game_id: str):
        self.game_connections[game_id].remove(websocket)
        if not self.game_connections[game_id]:
            del self.game_connections[game_id]

    async def broadcast_to_game(self, game_id: str, message: dict):
        if game_id in self.game_connections:
            for connection in self.game_connections[game_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/game/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await manager.connect(websocket, game_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast game updates to all connected clients
            await manager.broadcast_to_game(game_id, data)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, game_id)

@app.get("/")
async def home(request: Request, join: Optional[str] = Query(None), error: Optional[str] = Query(None)):
    """Render the home page or show join form if join parameter is present"""
    context = {"request": request}
    
    if error:
        context["error"] = "Game not found" if error == "game-not-found" else error
    
    if join:
        print(f"Attempting to join game {join}")
        print(f"Available games: {list(game.games.keys())}")
        game_data = game.games.get(join)
        if game_data:
            print(f"Game found: {game_data}")
            # Check if user is already a player in this game
            player_id = request.session.get(f"player_id_{join}")
            if player_id and any(p.id == player_id for p in game_data.players):
                # User is already a player, redirect to game
                return RedirectResponse(url=f"/game/{join}")
            
            if len(game_data.players) < 2:
                # Show join form with pre-filled game ID
                context["auto_join"] = join
                context["game"] = game_data
                return templates.TemplateResponse("lobby.html", context)
            else:
                # Game is full
                context["error"] = "Game is full"
                return templates.TemplateResponse("lobby.html", context)
        else:
            print(f"Game {join} not found")
            context["error"] = "Game not found"
    
    return templates.TemplateResponse("lobby.html", context)

@app.get("/waiting/{game_id}")
async def waiting_room(request: Request, game_id: str):
    """Render the waiting room page"""
    if game_id not in game.games:
        return RedirectResponse(url="/?error=game-not-found")
    
    game_data = game.games[game_id]
    if len(game_data.players) >= 2:
        return RedirectResponse(url=f"/game/{game_id}")
    
    # Try to get player ID from session or cookie
    player_id = request.session.get(f"player_id_{game_id}")
    if not player_id:
        player_id = request.cookies.get(f"player_id_{game_id}")
        if player_id:
            # If found in cookie but not in session, restore it to session
            request.session[f"player_id_{game_id}"] = player_id
    
    if not player_id:
        return RedirectResponse(url="/?error=session-expired")
    
    # Verify player is part of the game
    if not any(p.id == player_id for p in game_data.players):
        return RedirectResponse(url="/?error=not-in-game")
    
    return templates.TemplateResponse("waiting.html", {
        "request": request,
        "game_id": game_id,
        "game": game_data,
        "player_id": player_id
    })

@app.get("/game/{game_id}")
async def game_page(request: Request, game_id: str):
    """Render the game page"""
    game_data = game.games.get(game_id)
    if not game_data:
        return RedirectResponse(url="/?error=game-not-found")
    
    # Get player ID from session
    player_id = request.session.get(f"player_id_{game_id}")
    if not player_id:
        # No session found, redirect to join form
        return RedirectResponse(url=f"/?join={game_id}")
    
    # Verify player is part of the game
    if not any(p.id == player_id for p in game_data.players):
        # Player exists in session but not in game, redirect to join form
        return RedirectResponse(url=f"/?join={game_id}")
    
    return templates.TemplateResponse("game.html", {
        "request": request,
        "game": game_data,
        "player_id": player_id
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 