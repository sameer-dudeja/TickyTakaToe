import json
import os
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Dict, Optional
from ..models.game import Game, Player, PlayerMarker, GameStatus

router = APIRouter()

# File to store games
GAMES_FILE = "games.json"

# In-memory game storage (replace with database in production)
games: Dict[str, Game] = {}

def load_games():
    """Load games from file"""
    global games
    if os.path.exists(GAMES_FILE):
        with open(GAMES_FILE, 'r') as f:
            games_data = json.load(f)
            games = {
                game_id: Game.parse_obj(game_data)
                for game_id, game_data in games_data.items()
            }
    else:
        games = {}

def save_games():
    """Save games to file"""
    games_data = {
        game_id: game.dict()
        for game_id, game in games.items()
    }
    with open(GAMES_FILE, 'w') as f:
        json.dump(games_data, f)

# Load games at startup
load_games()

def render_game_content(request: Request, game: Game, player_id: str) -> str:
    """Helper function to render game content without base template"""
    from ..main import templates
    return templates.TemplateResponse(
        "game_content.html",  # We'll create this template
        {
            "request": request,
            "game": game,
            "player_id": player_id
        }
    )

@router.post("/games/create")
async def create_game(
    request: Request,
    player_name: str = Form(...),
    board_size: int = Form(3)
) -> Dict:
    """Create a new game and redirect to waiting room"""
    if not player_name:
        raise HTTPException(status_code=400, detail="Player name is required")
    
    try:
        game = Game.create_game(board_size)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create first player with X marker
    player = Player(name=player_name, marker=PlayerMarker.X)
    game.players.append(player)
    
    games[game.id] = game
    save_games()  # Save after creating game
    
    # Store player ID in session
    request.session[f"player_id_{game.id}"] = player.id
    
    # Return a redirect response with status code 303 (See Other)
    response = RedirectResponse(url=f"/waiting/{game.id}", status_code=303)
    response.set_cookie(
        key=f"player_id_{game.id}",
        value=player.id,
        httponly=True,
        max_age=3600,  # 1 hour
        samesite='lax'
    )
    return response

@router.get("/waiting/{game_id}")
async def waiting_room(request: Request, game_id: str):
    """Render the waiting room template"""
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return templates.TemplateResponse(
        "waiting.html",
        {"request": request, "game_id": game_id}
    )

@router.post("/games/{game_id}/join")
async def join_game(
    game_id: str,
    request: Request,
    player_name: str = Form(...),
) -> Dict:
    """Join an existing game"""
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if len(game.players) >= 2:
        raise HTTPException(status_code=400, detail="Game is full")
    
    if game.status != GameStatus.WAITING:
        raise HTTPException(status_code=400, detail="Game has already started")
    
    player = Player(name=player_name, marker=PlayerMarker.O)
    game.players.append(player)
    
    # Store player ID in session and save game state
    request.session[f"player_id_{game.id}"] = player.id
    save_games()
    
    # Send WebSocket notification about the new player
    from ..main import manager
    await manager.broadcast_to_game(game_id, {
        "type": "player_joined",
        "player_name": player_name,
        "player_id": player.id,
        "game_status": game.status,
        "players": [{"id": p.id, "name": p.name, "marker": p.marker.value} for p in game.players]
    })
    
    # If this is a form submission (not API call), redirect to waiting room first
    if request.headers.get("hx-request") != "true":
        response = RedirectResponse(url=f"/waiting/{game_id}", status_code=303)
        response.set_cookie(
            key=f"player_id_{game.id}",
            value=player.id,
            httponly=True,
            max_age=3600,  # 1 hour
            samesite='lax'
        )
        return response
    
    return {
        "player_id": player.id,
        "marker": player.marker,
        "game_status": game.status,
        "players": [{"id": p.id, "name": p.name, "marker": p.marker.value} for p in game.players]
    }

@router.post("/games/{game_id}/move")
async def make_move(
    game_id: str,
    request: Request,
    player_id: str = Form(...),
    row: int = Form(...),
    col: int = Form(...)
) -> HTMLResponse:
    """Make a move in the game"""
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Validate session
    session_player_id = request.session.get(f"player_id_{game_id}")
    if not session_player_id or session_player_id != player_id:
        raise HTTPException(status_code=403, detail="Invalid session")
    
    # Make the move
    if not game.make_move(player_id, row, col):
        raise HTTPException(status_code=400, detail="Invalid move")
    
    # Save game state
    save_games()
    
    # Send WebSocket notification about the move
    from ..main import manager
    await manager.broadcast_to_game(game_id, {
        "type": "move_made",
        "player_id": player_id,
        "row": row,
        "col": col,
        "game_status": game.status,
        "current_player": game.players[game.current_player_index].id,
        "board": game.board,
        "winner": game.winner,
        "players": [{"id": p.id, "name": p.name, "marker": p.marker.value} for p in game.players]
    })
    
    # Return updated game content
    return render_game_content(request, game, player_id)

@router.get("/games/{game_id}")
async def get_game_state(
    game_id: str,
    request: Request
) -> Dict:
    """Get the current state of the game"""
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get player ID from session
    player_id = request.session.get(f"player_id_{game_id}")
    if not player_id:
        raise HTTPException(status_code=403, detail="Invalid session")
    
    # Verify player is part of the game
    if not any(p.id == player_id for p in game.players):
        raise HTTPException(status_code=403, detail="Not a player in this game")
    
    # If it's an HTMX request or Accept header is text/html, return game content
    if request.headers.get("HX-Request") == "true" or "text/html" in request.headers.get("Accept", ""):
        return render_game_content(request, game, player_id)
    
    # Otherwise return JSON
    return {
        "board": game.board,
        "status": game.status,
        "current_player": game.players[game.current_player_index].id,
        "winner": game.winner,
        "players": [{"id": p.id, "name": p.name, "marker": p.marker.value} for p in game.players]
    }

@router.post("/games/{game_id}/start")
async def start_game(
    game_id: str,
    request: Request,
    player_id: str = Form(...)
) -> Dict:
    """Start the game - can only be called by the admin (first player)"""
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Validate session
    session_player_id = request.session.get(f"player_id_{game_id}")
    if not session_player_id or session_player_id != player_id:
        raise HTTPException(status_code=403, detail="Invalid session")
    
    if len(game.players) < 2:
        raise HTTPException(status_code=400, detail="Waiting for second player")
    
    if game.status != GameStatus.WAITING:
        raise HTTPException(status_code=400, detail="Game already started")
    
    # Check if the request is from the admin (first player)
    if game.players[0].id != player_id:
        raise HTTPException(status_code=403, detail="Only the game creator can start the game")
    
    game.status = GameStatus.IN_PROGRESS
    
    # Save game state
    save_games()
    
    # Send WebSocket notification about game start
    from ..main import manager
    await manager.broadcast_to_game(game_id, {
        "type": "game_started",
        "game_status": game.status,
        "current_player": game.players[game.current_player_index].id,
        "board": game.board,
        "players": [{"id": p.id, "name": p.name, "marker": p.marker.value} for p in game.players]
    })
    
    # Return updated game content for HTMX
    return render_game_content(request, game, player_id) 