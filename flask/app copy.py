from flask import Flask, render_template, request, redirect
import pandas as pd
import sqlite3
import os

# Flaskアプリケーションの初期化
app = Flask(__name__)
DB_NAME = "database.db"

# データベースセットアップ
def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contents TEXT,
        filename TEXT UNIQUE,
        link TEXT
    )
    """)
    conn.commit()
    conn.close()
    print("データベースがセットアップされました！")

# ホーム（検索画面）
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form['keyword']
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT filename, contents, link FROM files WHERE contents LIKE ? OR filename LIKE ?", ('%' + keyword + '%', '%' + keyword + '%'))
        results = cursor.fetchall()
        conn.close()
        return render_template('index.html', results=results)
    return render_template('index.html')

# 登録画面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        folder_path = request.form['folder_path']
        files = [file for file in os.listdir(folder_path) if file.endswith('.xlsx')]
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        for file in files:
            file_path = os.path.join(folder_path, file)
            try:
                df = pd.read_excel(file_path)
                contents = " ".join(df.astype(str).values.flatten())
                filename = file
                link = file_path
                cursor.execute("INSERT INTO files (contents, filename, link) VALUES (?, ?, ?)", (contents, filename, link))
            except sqlite3.IntegrityError:
                print(f"既に登録されているファイル: {file}")
        conn.commit()
        conn.close()
        return redirect('/register')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files")
    data = cursor.fetchall()
    conn.close()
    return render_template('register.html', data=data)

# アプリケーション起動
if __name__ == "__main__":
    setup_database()
    app.run(debug=True)