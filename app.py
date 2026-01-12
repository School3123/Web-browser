from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# シンプルなブラウザのUI（HTML）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Python Web Browser</title>
    <style>
        body { font-family: sans-serif; margin: 0; padding: 0; }
        .toolbar { background: #333; padding: 10px; color: white; display: flex; }
        input[type="text"] { flex: 1; padding: 8px; border-radius: 4px; border: none; }
        button { padding: 8px 15px; margin-left: 10px; cursor: pointer; }
        .content { width: 100%; height: 90vh; border: none; overflow: auto; padding: 20px; }
    </style>
</head>
<body>
    <div class="toolbar">
        <form method="post" style="display: flex; width: 100%;">
            <input type="text" name="url" placeholder="https://example.com" value="{{ url }}">
            <button type="submit">Go</button>
        </form>
    </div>
    <div class="content">
        {% if content %}
            {{ content | safe }}
        {% else %}
            <p>URLを入力してGoを押してください。 (例: https://www.wikipedia.org)</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    content = ""
    url = ""
    if request.method == 'POST':
        url = request.form.get('url')
        if not url.startswith('http'):
            url = 'https://' + url
        
        try:
            # 指定されたURLからコンテンツを取得
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 画像やCSSのリンクを絶対パスに書き換える（簡易版）
            for tag in soup.find_all(['img', 'link', 'script', 'a']):
                attr = 'href' if tag.name in ['link', 'a'] else 'src'
                if tag.has_attr(attr):
                    tag[attr] = urljoin(url, tag[attr])

            content = soup.prettify()
        except Exception as e:
            content = f"<p style='color:red;'>エラーが発生しました: {e}</p>"

    return render_template_string(HTML_TEMPLATE, content=content, url=url)

if __name__ == '__main__':
    # Codespacesで公開するために 0.0.0.0 で起動
    app.run(host='0.0.0.0', port=5000)
