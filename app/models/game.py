import uuid
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class PlayerMarker(str, Enum):
    X = "X"
    O = "O"

class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    marker: PlayerMarker

class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    board_size: int
    board: List[List[Optional[str]]]
    players: List[Player]
    current_player_index: int = 0
    status: GameStatus = GameStatus.WAITING
    winner: Optional[str] = None
    
    @classmethod
    def create_game(cls, board_size: int = 3) -> 'Game':
        """Create a new game with empty board"""
        if board_size < 3 or board_size > 5:
            raise ValueError("Board size must be between 3 and 5")
        
        board = [[None for _ in range(board_size)] for _ in range(board_size)]
        return cls(
            board_size=board_size,
            board=board,
            players=[]
        )
    
    def make_move(self, player_id: str, row: int, col: int) -> bool:
        """Make a move on the board"""
        # Validate game state
        if self.status != GameStatus.IN_PROGRESS:
            return False
            
        # Validate player turn
        if not self.players or len(self.players) < 2:
            return False
            
        current_player = self.players[self.current_player_index]
        if current_player.id != player_id:
            return False
            
        # Validate move coordinates
        if not self._is_valid_move(row, col):
            return False
            
        # Make the move
        self.board[row][col] = current_player.marker.value
        
        # Check for win or draw
        if self._check_winner(row, col, current_player.marker.value):
            self.status = GameStatus.FINISHED
            self.winner = current_player.id
        elif self._is_board_full():
            self.status = GameStatus.FINISHED
            self.winner = None  # Draw
        else:
            # Switch to next player
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            
        return True
    
    def _is_valid_move(self, row: int, col: int) -> bool:
        """Check if the move is valid"""
        return (
            0 <= row < self.board_size and
            0 <= col < self.board_size and
            self.board[row][col] is None and
            self.status == GameStatus.IN_PROGRESS
        )
    
    def _is_board_full(self) -> bool:
        """Check if the board is full"""
        return all(cell is not None for row in self.board for cell in row)
    
    def _check_winner(self, row: int, col: int, marker: str) -> bool:
        """Check if the last move resulted in a win"""
        # Check row
        if all(cell == marker for cell in self.board[row]):
            return True
            
        # Check column
        if all(self.board[r][col] == marker for r in range(self.board_size)):
            return True
            
        # Check diagonals
        if row == col and all(self.board[i][i] == marker for i in range(self.board_size)):
            return True
            
        if row + col == self.board_size - 1 and all(self.board[i][self.board_size-1-i] == marker for i in range(self.board_size)):
            return True
            
        return False
    
    class Config:
        json_encoders = {
            PlayerMarker: lambda v: v.value,
            GameStatus: lambda v: v.value
        } 