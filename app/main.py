from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS giochi (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome TEXT NOT NULL,
      numero_giocatori_massimo INTEGER NOT NULL,
      durata_media INTEGER NOT NULL,
      categoria TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS partite (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      gioco_id INTEGER NOT NULL,
      data DATE NOT NULL,
      vincitore TEXT NOT NULL,
      punteggio_vincitore INTEGER NOT NULL,
      FOREIGN KEY (gioco_id) REFERENCES giochi (id)
    );
    """)
    db.commit()

@app.before_first_request
def setup():
    init_db()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return redirect(url_for('list_games'))

@app.route('/games')
def list_games():
    db = get_db()
    cur = db.execute('SELECT * FROM giochi ORDER BY id')
    games = cur.fetchall()
    return render_template('games.html', games=games)

@app.route('/games/new', methods=['GET', 'POST'])
def new_game():
    if request.method == 'POST':
        nome = request.form['nome']
        numero = request.form['numero_giocatori_massimo'] or 0
        durata = request.form['durata_media'] or 0
        categoria = request.form['categoria']
        db = get_db()
        db.execute(
            'INSERT INTO giochi (nome, numero_giocatori_massimo, durata_media, categoria) VALUES (?, ?, ?, ?)',
            (nome, int(numero), int(durata), categoria)
        )
        db.commit()
        return redirect(url_for('list_games'))
    return render_template('new_game.html')

@app.route('/games/<int:game_id>/matches')
def list_matches(game_id):
    db = get_db()
    game = db.execute('SELECT * FROM giochi WHERE id = ?', (game_id,)).fetchone()
    if not game:
        return "Gioco non trovato", 404
    cur = db.execute('SELECT * FROM partite WHERE gioco_id = ? ORDER BY data DESC', (game_id,))
    matches = cur.fetchall()
    return render_template('matches.html', game=game, matches=matches)

@app.route('/games/<int:game_id>/matches/new', methods=['GET', 'POST'])
def new_match(game_id):
    db = get_db()
    game = db.execute('SELECT * FROM giochi WHERE id = ?', (game_id,)).fetchone()
    if not game:
        return "Gioco non trovato", 404
    if request.method == 'POST':
        data = request.form['data']
        vincitore = request.form['vincitore']
        punteggio = request.form['punteggio_vincitore'] or 0
        db.execute(
            'INSERT INTO partite (gioco_id, data, vincitore, punteggio_vincitore) VALUES (?, ?, ?, ?)',
            (game_id, data, vincitore, int(punteggio))
        )
        db.commit()
        return redirect(url_for('list_matches', game_id=game_id))
    return render_template('new_match.html', game=game)

if __name__ == '__main__':
    app.run(debug=True)