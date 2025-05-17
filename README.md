# TickyTakaToe 🎮

A modern take on the classic Tic Tac Toe game, built with HTMX and FastAPI. This project demonstrates how to create an interactive web game using modern web technologies while keeping the frontend simple and efficient.

## Features ✨

- **Variable Board Sizes**: Play on 3x3 to 5x5 grids
- **Multiple Match Formats**: 
  - Single Game
  - Best of 3
  - Best of 5
- **Real-time Updates**: Instant game state updates using HTMX
- **Custom Player Markers**: Choose your own game marker
- **Game Timer**: Keep track of move times
- **Waiting Room**: Queue system for player matching

## Tech Stack 🛠️

- **Frontend**:
  - HTMX for dynamic interactions
  - Custom CSS for styling
  - Minimal JavaScript
- **Backend**:
  - Python 3.x
  - FastAPI framework
  - Jinja2 templates
- **Infrastructure**:
  - AWS EC2 (planned)

## Getting Started 🚀

### Prerequisites

- Python 3.x
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/TickyTakaToe.git
   cd TickyTakaToe
   ```

2. Set up a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app/main.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## Project Structure 📁

```
TickyTakaToe/
├── app/
│   ├── api/         # API endpoints
│   ├── models/      # Game logic and data models
│   ├── templates/   # HTML templates
│   └── static/      # CSS and static files
├── terraform/       # Infrastructure as Code (planned)
└── docs/           # Documentation (planned)
```

## Contributing 🤝

Contributions are welcome! Feel free to:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

---
Made with ❤️ using HTMX and FastAPI 