import asyncio
import threading
import time
import base64
from flask import Flask, render_template_string, request, Response, jsonify
from playwright.async_api import async_playwright

app = Flask(__name__)

# --- 設定 ---
CONFIG = {
    "width": 1920,       # 解像度 (Full HD)
    "height": 1080,
    "port": 5000,
    "quality": 85        # JPEG画質 (85-90が最適。高いほど鮮明ですが通信が重くなります)
}

# ブラウザ状態管理
browser_state = {
    "page": None,
    "loop": None,
    "playwright": None,
    "browser": None
}

def run_async(coro):
    """FlaskのスレッドからPlaywright（非同期ループ）に命令を投げる"""
    future = asyncio.run_coroutine_threadsafe(coro, browser_state["loop"])
    return future.result()

async def setup_browser():
    """Firefoxの起動 (音声なし・高速)"""
    browser_state["playwright"] = await async_playwright().start()
    # headless=True にすることで、XvfbやFFmpegを使わずに最速で動作します
    browser_state["browser"] = await browser_state["playwright"].firefox.launch(headless=True)
    browser_state["page"] = await browser_state["browser"].new_page(
        viewport={'width': CONFIG["width"], 'height': CONFIG["height"]}
    )
    await browser_state["page"].goto("https://www.google.com")
    print("=== Firefox Engine Started (No Audio Mode) ===")

def start_event_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_browser())
    loop.run_forever()

# --- 映像ストリーミング (MJPEG) ---
def gen_frames():
    while True:
        if browser_state["page"]:
            try:
                # 非同期でスクリーンショットを取得
                async def get_shot():
                    return await browser_state["page"].screenshot(type='jpeg', quality=CONFIG["quality"])
                
                frame = run_async(get_shot())
                
                # MJPEG形式でパケットを送信
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                # 待機時間を短くして、なめらかな動きを実現 (約25fps)
                time.sleep(0.04) 
            except:
                continue

# --- ルート設定 ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, width=CONFIG["width"], height=CONFIG["height"])

@app.route('/video_feed')
def video_feed():
    """画像ストリームを供給するエンドポイント"""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/action')
def action():
    """操作転送用API"""
    atype = request.args.get('type')
    async def task():
        p = browser_state["page"]
        if not p: return
        try:
            if atype == 'click':
                await p.mouse.click(int(float(request.args.get('x'))), int(float(request.args.get('y'))))
            elif atype == 'key':
                await p.keyboard.press(request.args.get('key'))
            elif atype == 'scroll':
                await p.mouse.wheel(0, int(float(request.args.get('deltaY'))))
            elif atype == 'nav':
                url = request.args.get('url')
                if not url.startswith('http'): url = 'https://' + url
                await p.goto(url, wait_until="domcontentloaded")
        except: pass
    
    if browser_state["loop"]:
        asyncio.run_coroutine_threadsafe(task(), browser_state["loop"])
    return "ok"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>High Fidelity Remote Browser</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            margin: 0; padding: 0; background: #000; color: white; 
            font-family: sans-serif; display: flex; flex-direction: column; height: 100vh; overflow: hidden;
        }
        .toolbar { 
            padding: 8px 15px; background: #222; display: flex; gap: 10px; 
            height: 56px; align-items: center; border-bottom: 1px solid #333; z-index: 100;
        }
        input { 
            flex: 1; padding: 10px 15px; border-radius: 20px; border: 1px solid #444; 
            background: #333; color: white; outline: none;
        }
        button { 
            padding: 8px 18px; cursor: pointer; background: #007bff; color: white; 
            border: none; border-radius: 18px; font-weight: bold;
        }
        #view { 
            flex: 1; display: flex; justify-content: center; align-items: center; 
            background: #111; overflow: hidden; position: relative;
        }
        #screen { 
            max-width: 100%; max-height: 100%; object-fit: contain; cursor: crosshair;
            image-rendering: -webkit-optimize-contrast; /* ボヤけを軽減 */
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <input type="text" id="urlInput" placeholder="URLを入力して移動..." onkeydown="if(event.key==='Enter') navigate()">
        <button onclick="navigate()">移動</button>
    </div>
    <div id="view">
        <!-- 音声なし・映像のみのMJPEGストリーム -->
        <img id="screen" src="/video_feed" onclick="handleClick(event)">
    </div>
    <script>
        const screen = document.getElementById('screen');
        const BW = {{ width }};
        const BH = {{ height }};

        function navigate() {
            const url = document.getElementById('urlInput').value;
            fetch(`/action?type=nav&url=${encodeURIComponent(url)}`);
        }

        function handleClick(e) {
            const rect = screen.getBoundingClientRect();
            // クライアント上の表示サイズとサーバー解像度をマッピング
            const x = Math.round((e.clientX - rect.left) * (BW / rect.width));
            const y = Math.round((e.clientY - rect.top) * (BH / rect.height));
            fetch(`/action?type=click&x=${x}&y=${y}`);
        }

        window.onkeydown = function(e) {
            if (document.activeElement.tagName !== 'INPUT') {
                fetch(`/action?type=key&key=${encodeURIComponent(e.key)}`);
                if (["ArrowUp","ArrowDown"," "].includes(e.key)) e.preventDefault();
            }
        };

        screen.onwheel = function(e) {
            e.preventDefault();
            fetch(`/action?type=scroll&deltaY=${e.deltaY}`);
        };
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    # 専用スレッドでPlaywrightを開始
    loop = asyncio.new_event_loop()
    browser_state["loop"] = loop
    threading.Thread(target=start_event_loop, args=(loop,), daemon=True).start()
    
    # サーバー起動 (HTTPS)
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc', threaded=True)
