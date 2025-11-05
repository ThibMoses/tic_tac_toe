"""
Tic-Tac-Toe web app (Flask) — IA intermédiaire
- Lancez: pip install flask
- Exécutez: python tic_tac_toe_flask.py
- Ouvrez http://127.0.0.1:5000/

Fonctionnement : le client (JS) garde l'affichage, envoie le plateau actuel au serveur
POST /move avec JSON { board: [...], player: 'X' }
Le serveur calcule un coup IA (O) et renvoie { ai_move: index or -1, board: [...], status: 'ongoing'|'win'|'draw', winner: null|'X'|'O' }
"""
from flask import Flask, request, jsonify, render_template_string
import random

app = Flask(__name__)

# --- IA intermédiaire utilities ---
WIN_LINES = [
    (0,1,2),(3,4,5),(6,7,8),
    (0,3,6),(1,4,7),(2,5,8),
    (0,4,8),(2,4,6)
]


def check_winner(board):
    """Retourne 'X' ou 'O' si gagnant, 'draw' si match nul, ou None si partie en cours."""
    for a,b,c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(cell for cell in board):
        return 'draw'
    return None


def find_winning_move(board, symbol):
    """Si symbol peut gagner au prochain coup, retourner l'indice du coup gagnant. Sinon None."""
    for a,b,c in WIN_LINES:
        line = [board[a], board[b], board[c]]
        if line.count(symbol) == 2 and line.count('') == 1:
            empty_index = [a,b,c][line.index('')]
            return empty_index
    return None


def intermediate_ai_move(board, ai_symbol='O', player_symbol='X'):
    # 1) Gagner si possible
    move = find_winning_move(board, ai_symbol)
    if move is not None:
        return move
    # 2) Bloquer si le joueur peut gagner
    move = find_winning_move(board, player_symbol)
    if move is not None:
        return move
    # 3) Prendre le centre si libre
    if board[4] == '':
        return 4
    # 4) Prendre une case coin disponible
    corners = [0,2,6,8]
    available_corners = [c for c in corners if board[c] == '']
    if available_corners:
        return random.choice(available_corners)
    # 5) Prendre une case côté (edges)
    edges = [1,3,5,7]
    available_edges = [e for e in edges if board[e] == '']
    if available_edges:
        return random.choice(available_edges)
    # 6) Si rien d'autre, aucune case (plateau plein)
    return -1

# --- Routes ---
INDEX_HTML = '''
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Tic-Tac-Toe — IA intermédiaire (Flask)</title>
  <style>
    body{font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#f7f7fb}
    .board{display:grid;grid-template-columns:repeat(3,100px);gap:8px}
    .cell{width:100px;height:100px;display:flex;align-items:center;justify-content:center;font-size:40px;background:white;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.08);cursor:pointer}
    .cell.disabled{cursor:not-allowed;opacity:0.6}
    .controls{margin-left:24px}
    .container{display:flex;gap:24px}
    button{padding:10px 14px;border-radius:8px;border:0;background:#4f46e5;color:white;cursor:pointer}
    h1{margin:0 0 12px 0;font-size:20px}
    .status{margin-top:12px}
  </style>
</head>
<body>
  <div class="container">
    <div>
      <h1>Tic-Tac-Toe — tu es <strong>X</strong>, IA est <strong>O</strong></h1>
      <div class="board" id="board"></div>
      <div class="status" id="status">C'est à toi de jouer.</div>
    </div>
    <div class="controls">
      <button id="resetBtn">Recommencer</button>
      <div style="margin-top:10px">Astuce IA : elle joue « intermédiaire » — gagne si possible, bloque, prend le centre, puis coins.</div>
    </div>
  </div>

<script>
const boardEl = document.getElementById('board')
const statusEl = document.getElementById('status')
const resetBtn = document.getElementById('resetBtn')
let board = Array(9).fill('')
let gameOver = false

function render(){
  boardEl.innerHTML = ''
  board.forEach((cell, idx) => {
    const div = document.createElement('div')
    div.className = 'cell' + (cell || gameOver ? ' disabled' : '')
    div.textContent = cell
    div.addEventListener('click', () => onCellClick(idx))
    boardEl.appendChild(div)
  })
}

function onCellClick(idx){
  if (gameOver) return
  if (board[idx]) return
  // joueur joue X
  board[idx] = 'X'
  render()
  // vérifier si joueur a gagné ou match nul localement
  const localStatus = checkLocal(board)
  if (localStatus) return handleStatus(localStatus)
  // envoi au serveur pour que l'IA joue
  fetch('/move', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({board: board, player: 'X'})
  }).then(r=>r.json()).then(data=>{
    if (data.ai_move !== -1){
      board = data.board
    }
    handleStatus({status: data.status, winner: data.winner})
    render()
  }).catch(err=>{
    console.error(err)
    statusEl.textContent = 'Erreur serveur — voir la console.'
  })
}

function handleStatus(s){
  if (s.status === 'ongoing'){
    statusEl.textContent = "C'est à toi de jouer."
  } else if (s.status === 'draw'){
    statusEl.textContent = "Match nul !"
    gameOver = true
  } else if (s.status === 'win'){
    gameOver = true
    if (s.winner === 'X') statusEl.textContent = 'Bravo — tu as gagné !'
    else statusEl.textContent = "L'IA a gagné."
  }
}

function checkLocal(b){
  const lines = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
  for (const [a,b1,c] of lines){
    if (board[a] && board[a] === board[b1] && board[a] === board[c]){
      return {status:'win', winner: board[a]}
    }
  }
  if (board.every(x=>x)) return {status:'draw', winner: null}
  return null
}

resetBtn.addEventListener('click', ()=>{
  board = Array(9).fill('')
  gameOver = false
  statusEl.textContent = "C'est à toi de jouer."
  render()
})

// initial render
render()
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    board = data.get('board')
    player = data.get('player', 'X')
    # validate board
    if not isinstance(board, list) or len(board) != 9:
        return jsonify({'error': 'board must be list of 9 elements'}), 400
    # check current game state
    winner = check_winner(board)
    if winner == 'draw':
        return jsonify({'ai_move': -1, 'board': board, 'status': 'draw', 'winner': None})
    if winner in ('X','O'):
        return jsonify({'ai_move': -1, 'board': board, 'status': 'win', 'winner': winner})
    # compute ai move
    ai_symbol = 'O' if player == 'X' else 'X'
    ai_move = intermediate_ai_move(board, ai_symbol=ai_symbol, player_symbol=player)
    if ai_move == -1:
        # plateau plein
        status = 'draw'
        return jsonify({'ai_move': -1, 'board': board, 'status': status, 'winner': None})
    # apply ai move
    if board[ai_move] == '':
        board[ai_move] = ai_symbol
    # check new state
    winner_after = check_winner(board)
    if winner_after == 'draw':
        status = 'draw'
        winner_res = None
    elif winner_after in ('X','O'):
        status = 'win'
        winner_res = winner_after
    else:
        status = 'ongoing'
        winner_res = None
    return jsonify({'ai_move': ai_move, 'board': board, 'status': status, 'winner': winner_res})

if __name__ == '__main__':
    app.run(debug=True)
