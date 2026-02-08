from flask import Flask, Response, render_template_string, request
from flask_socketio import SocketIO
import threading, time
from threading import Lock

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Pygame Remote</title>
<style>
  body{margin:0;background:#000;color:#fff}
  #info{position:fixed;top:4px;left:6px;z-index:10}
  /* Prevent the browser from upscaling the streamed image — use its native size
     but allow it to shrink responsively to fit the viewport. */
  #stream{display:block;margin:0 auto;max-width:100%;height:auto;image-rendering:pixelated}
</style>
</head>
<body>
<div id="info">WASD / Arrows to move — click the canvas then use keys</div>
<img id="stream" src="/stream" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.1/socket.io.min.js"></script>
<script>
// Prefer websocket but allow polling fallback
const socket = io({transports:['websocket','polling']});
window._use_fallback = false;
socket.on('connect', () => {
    console.log('[remote_client] connected', socket.id);
    const info = document.getElementById('info'); if (info) info.textContent = 'Connected — click then use keys';
});
socket.on('disconnect', (reason) => {
    console.log('[remote_client] disconnected', reason);
    const info = document.getElementById('info'); if (info) info.textContent = 'Disconnected';
});
socket.on('connect_error', (err) => { console.warn('[remote_client] connect_error', err); window._use_fallback = true; const info = document.getElementById('info'); if (info) info.textContent = 'Socket failed — using HTTP fallback'; });
socket.on('reconnect_attempt', () => { console.log('[remote_client] reconnect_attempt'); });

window.addEventListener('keydown', e => {
    if (['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) return;
    // ensure page has focus; clicking the image helps
    e.preventDefault();
    console.log('[remote_client] keydown', e.key);
    try { socket.emit('key', {k: e.key, d: true}); } catch (e) {}
    // Always POST as a reliable fallback (non-blocking)
    fetch('/key', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({k: e.key, d: true})}).catch(err=>{/*ignore*/});
});
window.addEventListener('keyup', e => {
    if (['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) return;
    e.preventDefault();
    console.log('[remote_client] keyup', e.key);
    try { socket.emit('key', {k: e.key, d: false}); } catch (e) {}
    fetch('/key', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({k: e.key, d: false})}).catch(err=>{/*ignore*/});
});

// clicking the stream image focuses the window and hints the user to press keys
document.getElementById('stream').addEventListener('click', () => {
    window.focus();
    const info = document.getElementById('info'); if (info) info.textContent = 'Canvas focused — press keys';
});
</script>
</body>
</html>
"""

# remote key state and lock
_REMOTE_KEYS = set()
_REMOTE_STATE = {}  # key -> (down:bool, last_ts:float)
_LOCK = Lock()
_KEY_TIMEOUT = 0.6  # seconds: consider a key released if no update within this
# number of connected socket.io clients (used to suspend streaming when zero)
_CLIENT_COUNT = 0

@socketio.on('connect')
def _on_connect():
    global _CLIENT_COUNT
    _CLIENT_COUNT += 1
    print(f"[remote_server] client connected (total={_CLIENT_COUNT})")

@socketio.on('key')
def _on_key(data):
    k = data.get('k')
    down = bool(data.get('d'))
    if not k:
        return
    # Normalize simple letter keys to lowercase so mapping is consistent
    try:
        if isinstance(k, str) and len(k) == 1:
            k = k.lower()
    except Exception:
        pass
    now = time.time()
    print(f"[remote_server] key event: {k} down={down}")
    with _LOCK:
        # update state with timestamp; we'll derive pressed keys from this map
        _REMOTE_STATE[k] = (bool(down), now)
        # keep a convenience set for backward compatibility
        if down:
            _REMOTE_KEYS.add(k)
        else:
            _REMOTE_KEYS.discard(k)


@socketio.on('disconnect')
def _on_disconnect():
    global _CLIENT_COUNT
    try:
        _CLIENT_COUNT = max(0, _CLIENT_COUNT - 1)
    except Exception:
        _CLIENT_COUNT = 0
    print(f"[remote_server] client disconnected (total={_CLIENT_COUNT})")

def get_remote_keys():
    now = time.time()
    keys = set()
    with _LOCK:
        # derive keys considered pressed: those with down=True and recent timestamp
        to_remove = []
        for k, (down, ts) in list(_REMOTE_STATE.items()):
            if down and (now - ts) <= _KEY_TIMEOUT:
                keys.add(k)
            elif not down:
                # explicit release: remove state
                to_remove.append(k)
            elif (now - ts) > _KEY_TIMEOUT:
                # stale entry: treat as released and remove
                to_remove.append(k)
        for k in to_remove:
            _REMOTE_STATE.pop(k, None)
            _REMOTE_KEYS.discard(k)
    return keys


def make_stream(get_frame_bytes, fps=6):
    def gen():
        delay = 1.0 / max(1, fps)
        while True:
            try:
                if _CLIENT_COUNT <= 0:
                    time.sleep(0.25)
                    continue
            except Exception:
                pass

            try:
                frame = get_frame_bytes()
            except Exception:
                frame = None

            if not frame:
                time.sleep(delay); continue

            try:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"[remote_server] stream yield error: {e}")
            time.sleep(delay)
    return gen


def start_server(get_frame_bytes, host='0.0.0.0', port=5000, fps=6, scale=0.5, quality=50):
    @app.route('/')
    def index():
        return render_template_string(HTML)

    @app.route('/stream')
    def stream():
        return Response(make_stream(get_frame_bytes, fps)(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/key', methods=['POST'])
    def key_endpoint():
        try:
            data = request.get_json(force=True)
        except Exception:
            data = {}
        if data:
            print(f"[remote_server] HTTP key receive: {data}")
            _on_key(data)
        return '', 204

    # allow simple CORS for the POST fallback
    @app.after_request
    def _add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    def _run():
        try:
            print(f"[remote_server] socketio starting on {host}:{port}")
            socketio.run(app, host=host, port=port, debug=False)
        except Exception as e:
            print(f"[remote_server] socketio failed: {e}")

    # attach generator parameters via closure
    app._stream_gen = make_stream(get_frame_bytes, fps=fps)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    print(f"[remote_server] thread started (target {host}:{port})")
    return t
