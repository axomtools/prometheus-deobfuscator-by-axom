import sys
import json
import webbrowser
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from main import clean
from trace import on as traceon

page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Deobf</title>
<style>
* { box-sizing: border-box; }
body { margin: 0; padding: 24px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0e1014; color: #e6e8eb; min-height: 100vh; }
h1 { margin: 0 0 4px; font-size: 22px; font-weight: 600; }
p.sub { color: #8b95a3; font-size: 13px; margin: 0 0 20px; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; height: calc(100vh - 180px); min-height: 400px; }
.col { display: flex; flex-direction: column; min-height: 0; }
.bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #8b95a3; font-weight: 600; }
.tools { display: flex; gap: 8px; }
textarea { flex: 1; width: 100%; padding: 14px; background: #16191f; color: #e6e8eb; border: 1px solid #262a33; border-radius: 10px; font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 13px; line-height: 1.55; resize: none; outline: none; }
textarea:focus { border-color: #4a7cff; }
button { background: #22262e; color: #e6e8eb; border: 1px solid #2e333d; padding: 7px 14px; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; font-family: inherit; }
button:hover { background: #2b303a; border-color: #3a404c; }
button:active { transform: scale(0.97); }
button.act { background: #4a7cff; border-color: #4a7cff; color: #fff; }
button.act:hover { background: #5b88ff; border-color: #5b88ff; }
button:disabled { opacity: 0.4; cursor: not-allowed; }
.foot { display: flex; gap: 10px; margin-top: 16px; align-items: center; }
.note { color: #8b95a3; font-size: 12px; margin-left: auto; max-width: 60%; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }
.note.ok { color: #4ade80; }
.note.bad { color: #f87171; }
input[type=file] { display: none; }
@media (max-width: 720px) { .row { grid-template-columns: 1fr; height: auto; } .col { height: 300px; } }
</style>
</head>
<body>
<h1>Deobf</h1>
<p class="sub">Paste Prometheus-obfuscated Lua or upload a file, then click Deobf.</p>
<div class="row">
  <div class="col">
    <div class="bar">
      <span class="label">Input</span>
      <div class="tools">
        <button id="load">Upload</button>
        <button id="wipe">Clear</button>
      </div>
    </div>
    <textarea id="src" placeholder="Paste obfuscated Lua here..."></textarea>
    <input type="file" id="pick" accept=".lua,.luau,.txt">
  </div>
  <div class="col">
    <div class="bar">
      <span class="label">Output</span>
      <div class="tools">
        <button id="copy" disabled>Copy</button>
        <button id="save" disabled>Download</button>
      </div>
    </div>
    <textarea id="out" placeholder="Deobfuscated code appears here..." readonly></textarea>
  </div>
</div>
<div class="foot">
  <button class="act" id="deobf">Deobf</button>
  <span class="note" id="note"></span>
</div>
<script>
const pick = (id) => document.getElementById(id);
function say(text, cls) {
  const e = pick('note');
  e.textContent = text;
  e.title = text;
  e.className = 'note' + (cls ? ' ' + cls : '');
}
pick('load').onclick = () => pick('pick').click();
pick('pick').onchange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const rd = new FileReader();
  rd.onload = () => { pick('src').value = rd.result; say('loaded ' + file.name, 'ok'); };
  rd.readAsText(file);
  e.target.value = '';
};
pick('wipe').onclick = () => {
  pick('src').value = '';
  pick('out').value = '';
  pick('copy').disabled = true;
  pick('save').disabled = true;
  say('');
};
pick('deobf').onclick = async () => {
  const text = pick('src').value;
  if (!text.trim()) { say('nothing to do', 'bad'); return; }
  say('working...');
  let res;
  try {
    res = await fetch('/work', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
  } catch (err) {
    say('network: ' + err.message, 'bad');
    return;
  }
  let data = {};
  try {
    data = await res.json();
  } catch (err) {
    say('bad response from server', 'bad');
    return;
  }
  if (!res.ok || data.error) {
    say(data.error || ('server ' + res.status), 'bad');
    return;
  }
  pick('out').value = data.text;
  pick('copy').disabled = false;
  pick('save').disabled = false;
  if (data.notes && data.notes.length) {
    say('done - ' + data.notes.join('; '), 'ok');
  } else {
    say('done', 'ok');
  }
};
pick('copy').onclick = async () => {
  const text = pick('out').value;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    say('copied', 'ok');
  } catch (err) {
    pick('out').select();
    document.execCommand('copy');
    say('copied', 'ok');
  }
};
pick('save').onclick = () => {
  const text = pick('out').value;
  if (!text) return;
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'clean.luau';
  link.click();
  URL.revokeObjectURL(url);
  say('saved', 'ok');
};
</script>
</body>
</html>
"""


class door(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            body = page.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != '/work':
            self.send_error(404)
            return
        try:
            size = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(size).decode('utf-8')
            payload = json.loads(raw)
            src = payload.get('text', '')
            if not isinstance(src, str):
                raise ValueError('text must be a string')
            out, note = clean(src)
            body = json.dumps({'text': out, 'notes': note['notes']}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            tb = traceback.format_exc()
            sys.stderr.write(tb)
            sys.stderr.flush()
            name = e.__class__.__name__
            text = str(e)
            if text:
                msg = name + ': ' + text
            else:
                msg = name
            body = json.dumps({'error': msg}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def run(host='127.0.0.1', port=8899):
    server = HTTPServer((host, port), door)
    url = 'http://%s:%d/' % (host, server.server_address[1])
    print('running at ' + url)
    print('debug trace is on - every scan/read/wash step prints to this terminal')
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('')
        server.server_close()


if __name__ == '__main__':
    run()
