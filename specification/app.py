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
    model_list = df["model"].unique()
    model_dict = df.set_index("model").T.to_dict()  # データを辞書形式に変換

    print(df)  # モデルデータをデバッグ用に出力
    return render_template('index.html', table=model_dict, models=model_list)



@app.route('/register', methods=['GET', 'POST'])
def register():
    connection = get_db_connection()
    try:
        if request.method == 'POST':
            file_path = request.form.get('file_path')
            if file_path:
                try:
                    df = pd.read_csv(file_path)
                    with connection:
                        for _, row in df.iterrows():
                            connection.execute(
                                'INSERT INTO spec (model, speed, price) VALUES (?, ?, ?)',
                                (row['model'], row['speed'], row['price'])
                            )
                except Exception as e:
                    print(f"Error: {e}")
            return redirect('/register')

        # Fetch distinct models and table data
        models = connection.execute('SELECT DISTINCT model FROM spec').fetchall()
        rows = connection.execute('SELECT model, speed, price FROM spec').fetchall()

        # Prepare data in a dictionary format
        model_data = {row['model']: {'speed': row['speed'], 'price': row['price']} for row in rows}

    finally:
        connection.close()

    return render_template(
        'register.html',
        models=[model[0] for model in models],
        table=model_data
    )


if __name__ == '__main__':
    initialize_db()
    app.run(debug=True, port=5001)
