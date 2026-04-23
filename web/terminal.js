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

  // Line-edited local input with local echo. The server is line-oriented
  // (readuntil LF) and does no echo, so without this the user types into
  // a void. We accumulate characters client-side, echo them to the
  // terminal, handle backspace, and only transmit when Enter is pressed
  // (sending '\r\n' because xterm sends bare '\r' for Enter but the
  // server's readuntil wants '\n').
  let buf = '';

  term.onData((data) => {
    if (ws.readyState !== WebSocket.OPEN) return;

    for (const ch of data) {
      const code = ch.charCodeAt(0);

      if (ch === '\r' || ch === '\n') {
        // Submit the line.
        term.write('\r\n');
        ws.send(new TextEncoder().encode(buf + '\r\n'));
        buf = '';
      } else if (ch === '\x7f' || ch === '\b') {
        // Backspace / DEL — rub out one char.
        if (buf.length > 0) {
          buf = buf.slice(0, -1);
          term.write('\b \b');
        }
      } else if (ch === '\x03') {
        // Ctrl-C — discard the current line, show ^C.
        term.write('^C\r\n');
        buf = '';
      } else if (code >= 0x20 && code !== 0x7f) {
        // Printable.
        buf += ch;
        term.write(ch);
      }
      // Ignore other control chars (arrow keys, function keys, etc).
    }
  });
})();
