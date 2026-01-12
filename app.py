import asyncio
import threading
import time
import base64
from flask import Flask, render_template_string, request, Response
from playwright.async_api import async_playwright

app = Flask(__name__)

# ブラウザ管理用 (高品質設定)
browser_info = {
    "page": None,
    "loop": None,
    "playwright": None,
    "browser": None,
    "width": 1920,   # 基本解像度
    "height": 1080
}

def run_async(coro):
    future = asyncio.run_coroutine_threadsafe(coro, browser_info["loop"])
    return future.result()

async def setup_browser():
    browser_info["playwright"] = await async_playwright().start()
    browser_info["browser"] = await browser_info["playwright"].firefox.launch(headless=True)
    browser_info["page"] = await browser_info["browser"].new_page(
        viewport={'width': browser_info["width"], 'height': browser_info["height"]}
    )
    await browser_info["page"].goto("https://www.google.com")
    print("Firefox Responsive Mode 起動完了")

def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_browser())
    loop.run_forever()

def gen_frames():
    while True:
        try:
            async def get_shot():
                return await browser_info["page"].screenshot(type='jpeg', quality=85)
            frame = run_async(get_shot())
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.05)
        except:
            break

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, width=browser_info["width"], height=browser_info["height"])

# --- 操作系 ---
@app.route('/navigate')
def navigate():
    url = request.args.get('url')
    if url:
        if not url.startswith('http'): url = 'https://' + url
        run_async(browser_info["page"].goto(url, wait_until="domcontentloaded"))
    return "ok"

@app.route('/action')
def action():
    atype = request.args.get('type')
    async def task():
        if atype == 'click':
            await browser_info["page"].mouse.click(int(float(request.args.get('x'))), int(float(request.args.get('y'))))
        elif atype == 'key':
            await browser_info["page"].keyboard.press(request.args.get('key'))
        elif atype == 'scroll':
            await browser_info["page"].mouse.wheel(0, int(float(request.args.get('deltaY'))))
    run_async(task())
    return "ok"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Fluid Python Browser</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            margin: 0; 
            padding: 0;
            background: #000; 
            color: white; 
            font-family: sans-serif; 
            display: flex;
            flex-direction: column;
            height: 100vh; /* 画面全体の高さ */
            overflow: hidden;
        }
        .toolbar { 
            padding: 10px; 
            background: #222; 
            display: flex; 
            gap: 10px; 
            height: 60px;
            align-items: center;
        }
        input { 
            flex: 1; 
            padding: 12px; 
            border-radius: 4px; 
            border: none; 
            background: #444; 
            color: white; 
            font-size: 16px;
        }
        button { 
            padding: 10px 20px; 
            cursor: pointer; 
            background: #007bff; 
            color: white; 
            border: none; 
            border-radius: 4px; 
            font-weight: bold;
        }
        #viewport { 
            flex: 1; /* 残りの空間をすべて使う */
            display: flex;
            justify-content: center;
            align-items: center;
            background: #111;
            position: relative;
            overflow: hidden;
        }
        #screen { 
            max-width: 100%; 
            max-height: 100%; 
            width: auto;
            height: auto;
            object-fit: contain; /* アスペクト比を維持してフィット */
            cursor: crosshair;
            image-rendering: -webkit-optimize-contrast;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <input type="text" id="urlInput" placeholder="https://www.google.com" onkeydown="if(event.key==='Enter') navigate()">
        <button onclick="navigate()">Go</button>
    </div>
    <div id="viewport">
        <img id="screen" src="/video_feed" onclick="handleClick(event)">
    </div>

    <script>
        const screen = document.getElementById('screen');
        const BW = {{ width }};  // 1920
        const BH = {{ height }}; // 1080

        function navigate() {
            fetch("/navigate?url=" + encodeURIComponent(document.getElementById('urlInput').value));
        }
        
        function handleClick(e) {
            const rect = screen.getBoundingClientRect();
            // 表示されているサイズから、サーバー側の解像度（1920x1080）上の座標に正しく変換
            const x = Math.round((e.clientX - rect.left) * (BW / rect.width));
            const y = Math.round((e.clientY - rect.top) * (BH / rect.height));
            fetch(`/action?type=click&x=${x}&y=${y}`);
        }

        screen.onwheel = function(e) {
            e.preventDefault();
            fetch(`/action?type=scroll&deltaY=${e.deltaY}`);
        };

        window.onkeydown = function(e) {
            if (document.activeElement.tagName !== 'INPUT') {
                fetch(`/action?type=key&key=${e.key}`);
            }
        };
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    browser_info["loop"] = loop
    t = threading.Thread(target=start_background_loop, args=(loop,), daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc', threaded=True)
