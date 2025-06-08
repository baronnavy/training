from flask import Flask, render_template, request, redirect
from markupsafe import Markup
import pandas as pd
import psycopg2
import os
import csv
import re

app = Flask(__name__)

# PostgreSQL接続情報
DB_HOST = "localhost"
DB_NAME = "flask"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

# 類似語辞書の読み込み
def load_synonyms_dict(file_path):
    # CSVをDataFrameとして読み込み
    df = pd.read_csv(file_path, encoding='utf-8')
    # DataFrameを辞書形式に変換
    synonyms_dict = df.groupby('keyword')['synonym'].apply(list).to_dict()

    print(synonyms_dict)  # 作成された辞書を出力
    return synonyms_dict

synonyms_dict = load_synonyms_dict('synonyms.csv')

# データベースセットアップ
def setup_database():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_search (
        id SERIAL PRIMARY KEY,
        contents TEXT,
        filename TEXT UNIQUE,
        link TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS master (
        id SERIAL PRIMARY KEY,
        filename TEXT UNIQUE,
        category TEXT
    );
    """)
    conn.commit()
    conn.close()
    print("データベースがセットアップされました！")

# ホーム画面（検索機能）
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form['keyword']
        related_words = [keyword] + synonyms_dict.get(keyword, [])
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()

        # 動的にSQLクエリを構築
        query_conditions = " OR ".join([f"document_search.contents LIKE '%{word}%' OR document_search.filename LIKE '%{word}%'" for word in related_words])
        query = f"""
        SELECT 
            document_search.filename, 
            document_search.contents, 
            document_search.link, 
            master.category
        FROM 
            document_search
        JOIN 
            master
        ON 
            document_search.filename = master.filename
        WHERE 
            {query_conditions};
        """
        print("生成されたクエリ:", query)
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        # ハイライト処理
        highlighted_results = []
        for result in results:
            highlighted_content = re.sub(f'({"|".join(map(re.escape, related_words))})', r'<mark>\1</mark>', result[1], flags=re.IGNORECASE)
            highlighted_results.append((result[0], Markup(highlighted_content), result[2], result[3]))
        
        return render_template('index.html', results=highlighted_results, keyword=keyword)
    return render_template('index.html', results=None)

# 登録画面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        folder_path = request.form['folder_path']
        files = [file for file in os.listdir(folder_path) if file.endswith('.xlsx')]
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        for file in files:
            file_path = os.path.join(folder_path, file)
            try:
                df = pd.read_excel(file_path)
                contents = " ".join(df.astype(str).values.flatten())
                filename = file
                link = file_path
                cursor.execute("INSERT INTO document_search (contents, filename, link) VALUES (%s, %s, %s)", (contents, filename, link))
            except psycopg2.Error as e:
                print(f"エラー発生: {e}")
        conn.commit()
        conn.close()
        return redirect('/register')
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM document_search")
    data = cursor.fetchall()
    conn.close()
    return render_template('register.html', data=data)

# アプリケーション起動
if __name__ == "__main__":
    setup_database()
    app.run(debug=True)
