from flask import Flask, render_template, request, redirect
import sqlite3
import pandas as pd

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

@app.route('/')
def index():
    connection = get_db_connection()
    rows = connection.execute('SELECT model, speed, price FROM spec').fetchall()
    connection.close()

    # pandasでデータフレーム化
    df = pd.DataFrame(rows, columns=["model", "speed", "price"])

    # ピボット処理
    df_pivot = df.set_index("model").T

    # AAAモデルの基準値を取得
    base_model = df[df['model'] == 'AAA']
    base_speed = base_model['speed'].values[0]
    base_price = base_model['price'].values[0]

    # スタイル付け関数
    def highlight_cells(val, base):
        if isinstance(val, (int, float)):  # 数値であることを確認
            return 'background-color: blue; color: white;' if val > base else 'background-color: red; color: white;'
        return ''  # 数値以外はスタイルなし

    # テーブルに色付けを適用
    styled_table = {}
    for row_name, row_values in df_pivot.iterrows():
        styled_table[row_name] = []
        for col_name, col_value in zip(df_pivot.columns, row_values):
            style = highlight_cells(col_value, base_speed if row_name == 'speed' else base_price)
            styled_table[row_name].append({'model': col_name, 'value': col_value, 'style': style})

    return render_template('index.html', table=styled_table)

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
