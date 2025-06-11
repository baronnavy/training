from flask import Flask, render_template, request, redirect
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import json
import matplotlib
import plotly

matplotlib.use('Agg')  # GUI非依存のバックエンドに設定

app = Flask(__name__)

# データベースの初期化
def initialize_db():
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spec (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            speed INTEGER,
            price INTEGER
        )
    ''')
    connection.commit()
    connection.close()

def get_db_connection():
    connection = sqlite3.connect('data.db')
    connection.row_factory = sqlite3.Row
    return connection

@app.route('/graph', methods=['GET', 'POST'])
def graph():
    graph_json = None  # 初期値を設定

    if request.method == 'POST':
        connection = get_db_connection()
        rows = connection.execute('SELECT model, speed, price FROM spec').fetchall()
        connection.close()

        df = pd.DataFrame(rows, columns=["model", "speed", "price"])
        x_axis = request.form['x_axis']
        y_axis = request.form['y_axis']

        # 散布図生成
        graph_figure = {
            'data': [{
                'x': df[x_axis].tolist(),
                'y': df[y_axis].tolist(),
                'type': 'scatter',
                'mode': 'markers'
            }],
            'layout': {
                'title': f'{x_axis.capitalize()} vs {y_axis.capitalize()}',
                'xaxis': {'title': x_axis.capitalize()},
                'yaxis': {'title': y_axis.capitalize()}
            }
        }
        graph_json = json.dumps(graph_figure)  # graph_jsonを更新

    return render_template('graph.html', graph_json=graph_json)


    

@app.route('/')
def index():
    connection = get_db_connection()
    rows = connection.execute('SELECT model, speed, price FROM spec').fetchall()
    connection.close()

    df = pd.DataFrame(rows, columns=["model", "speed", "price"])
    df_pivot = df.set_index("model").T.to_dict()

    return render_template('index.html', table=df_pivot)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        file_path = request.form.get('file_path')
        if file_path:
            try:
                df = pd.read_csv(file_path)
                connection = get_db_connection()
                for _, row in df.iterrows():
                    connection.execute(
                        'INSERT INTO spec (model, speed, price) VALUES (?, ?, ?)',
                        (row['model'], row['speed'], row['price'])
                    )
                connection.commit()
            except Exception as e:
                print(f"エラー: {e}")
            finally:
                connection.close()
        return redirect('/register')

    connection = get_db_connection()
    rows = connection.execute('SELECT * FROM spec').fetchall()
    connection.close()
    return render_template('register.html', spec=rows)

if __name__ == '__main__':
    initialize_db()
    app.run(debug=True, port=5001)
