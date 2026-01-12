from flask import Flask, render_template_string, request, Response
from playwright.sync_api import sync_playwright
import time
import traceback

app = Flask(__name__)

# ブラウザ状態管理
state = {"pw": None, "browser": None, "page": None}

def startup():
    if state["page"] is None:
        try:
            print("--- ブラウザ起動中 (高速モード) ---")
            state["pw"] = sync_playwright().start()
            state["browser"] = state["pw"].chromium.launch(
                headless=True, 
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            state["page"] = state["browser"].new_page(viewport={'width': 1280, 'height': 720})
            state["page"].goto("https://www.google.com")
            print("--- 起動成功 ---")
        except Exception as e:
            print(traceback.format_exc())
            raise e

@app.route('/')
def index():
    startup()
    return render_template_string(HTML_TEMPLATE)

@app.route('/screenshot')
def screenshot():
    if state["page"]:
        try:
            # 速度優先のため画質を50に調整。これで転送が速くなります。
            img = state["page"].screenshot(type='jpeg', quality=50)
            return Response(img, mimetype='image/jpeg')
        except:
            return "", 500
    return "", 404

@app.route('/navigate')
def navigate():
    url = request.args.get('url')
    if url and state["page"]:
        if not url.startswith('http'): url = 'https://' + url
        try: state["page"].goto(url, wait_until="domcontentloaded", timeout=10000)
        except: pass
    return "ok"

@app.route('/action')
def action():
    atype = request.args.get('type')
    page = state["page"]
    if not page: return "error"
    try:
        if atype == 'click':
            page.mouse.click(int(float(request.args.get('x'))), int(float(request.args.get('y'))))
        elif atype == 'key':
            page.keyboard.press(request.args.get('key'))
        elif atype == 'scroll':
            # スクロール感度を調整
            dy = int(float(request.args.get('deltaY')))
            page.mouse.wheel(0, dy)
    except: pass
    return "ok"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Fast Python Browser</title>
    <style>
        * { -webkit-user-select: none; user-select: none; -webkit-touch-callout: none; }
        body { margin: 0; background: #000; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        .toolbar { padding: 10px; background: #333; display: flex; gap: 5px; }
        input { flex: 1; padding: 12px; border-radius: 4px; background: #eee; font-size: 16px; user-select: text; }
        #screen-container { flex: 1; display: flex; justify-content: center; align-items: center; background: #111; position: relative; }
        #screen { max-width: 100%; max-height: 100%; object-fit: contain; cursor: crosshair; -webkit-user-drag: none; }
    </style>
</head>
<body>
    <div class="toolbar">
        <input type="text" id="url" placeholder="URL検索" onkeydown="if(event.key==='Enter') nav()">
        <button onclick="nav()" style="padding:10px 20px;">Go</button>
    </div>
    <div id="screen-container">
        <img id="screen" src="/screenshot" oncontextmenu="return false;" onclick="clk(event)" draggable="false">
    </div>

    <script>
        const s = document.getElementById('screen');
        
        // --- 高速リロードの核心コード ---
        function updateScreen() {
            const nextImg = new Image();
            nextImg.onload = function() {
                // 読み込みが完了したら実際の画面を差し替え、即座に次をリクエスト
                s.src = this.src;
                requestAnimationFrame(updateScreen); 
            };
            nextImg.onerror = function() {
                // エラー時は少し待ってから再開
                setTimeout(updateScreen, 500);
            };
            nextImg.src = "/screenshot?t=" + Date.now();
        }

        // 初回起動
        updateScreen();

        function nav() { fetch("/navigate?url=" + encodeURIComponent(document.getElementById('url').value)); }
        
        function clk(e) {
            const r = s.getBoundingClientRect();
            const x = Math.round((e.clientX - r.left) * (1280 / r.width));
            const y = Math.round((e.clientY - r.top) * (720 / r.height));
            fetch(`/action?type=click&x=${x}&y=${y}`);
        }

        s.onwheel = (e) => {
            e.preventDefault();
            fetch(`/action?type=scroll&deltaY=${e.deltaY}`);
        };

        window.onkeydown = (e) => {
            if(document.activeElement.id !== 'url') {
                fetch(`/action?type=key&key=${e.key}`);
            }
        };
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    # threaded=Falseにより、リクエストが順番に処理されるため、
    # 読み込んだ瞬間に次を呼ぶこの方式が最も安定します。
    app.run(host='0.0.0.0', port=5000, threaded=False)
