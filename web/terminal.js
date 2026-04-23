// Terminal emulator for the V9N Voyager 1 Emulator.
// Connects the xterm.js terminal to the WebSocket bridge that relays
// bytes to the upstream raw-TCP server.

(() => {
  const term = new Terminal({
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
    fontSize: 14,
    cursorBlink: true,
    convertEol: false,
    theme: {
      background: '#0a0e14',
      foreground: '#c5d1e0',
      cursor: '#ff9f43',
      selectionBackground: '#2a3441',
    },
  });
  const fit = new FitAddon.FitAddon();
  term.loadAddon(fit);
  term.open(document.getElementById('terminal'));
  fit.fit();
  window.addEventListener('resize', () => fit.fit());

  const statusEl = document.getElementById('status');
  function setStatus(text, cls) {
    statusEl.textContent = text;
    statusEl.className = 'status' + (cls ? ' ' + cls : '');
  }

  const wsProto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${wsProto}//${location.host}/ws`);
  ws.binaryType = 'arraybuffer';

  ws.addEventListener('open', () => {
    setStatus('connected', 'open');
    term.focus();
  });

  ws.addEventListener('message', (ev) => {
    let bytes;
    if (typeof ev.data === 'string') {
      bytes = new TextEncoder().encode(ev.data);
    } else {
      bytes = new Uint8Array(ev.data);
    }
    term.write(bytes);
  });

  ws.addEventListener('close', (ev) => {
    setStatus(`closed (${ev.code})`, 'err');
    term.write('\r\n\x1b[31m[connection closed]\x1b[0m\r\n');
  });

  ws.addEventListener('error', () => {
    setStatus('error', 'err');
  });

  // Send keystrokes as raw bytes. Terminal sends '\r' for Enter; the server
  // accepts CR, LF, or CRLF, so forward verbatim.
  term.onData((data) => {
    if (ws.readyState !== WebSocket.OPEN) return;
    ws.send(new TextEncoder().encode(data));
  });
})();
