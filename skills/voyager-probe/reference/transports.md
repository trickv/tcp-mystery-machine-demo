# Transports (skill reference)

Audience: Claude Code executing the voyager-probe skill. Imperative,
minimal, no OS hand-holding.

Target: `voyager1.v9n.us:4242` (override via `$VOYAGER_HOST`). Raw
TCP, CRLF line-oriented. Server sends a banner + `> ` prompt; reply
framing is one-line (no terminator) or multi-line (terminated by a
line containing just `.`). Errors: `?CMD`, `?SYNTAX`, `?BUSY`,
`?OVF`, `?TIMEOUT`, `?SHUTDOWN`.

## Selection order

Try in this order; stop at the first one that works.

1. `nc` — most common on Unix-like hosts.
2. `ncat` (nmap) — fallback if `nc` is absent.
3. `python3` — fallback for Windows / locked-down shells.
4. `node` — fallback if Python is absent but Node is present.

Do **not** use interactive `telnet` from the skill; it's meant for
humans. Do **not** hold sockets open across Bash calls (each tool
invocation is its own subprocess). Do **not** assume the flavor of
`nc` — detect.

## Detect nc flavor first

```sh
if nc -h 2>&1 | grep -q -- '-q'; then NC_ARGS="-q 1"
else NC_ARGS="-w 2"; fi
```

- OpenBSD nc (most Linux): `-q 1` exits 1s after stdin closes.
- BSD nc (macOS): no `-q`, use `-w 2`.
- GNU netcat (rare): use `-c`.

## One-shot query (preferred)

```sh
echo 'STATUS' | nc $NC_ARGS "${VOYAGER_HOST:-voyager1.v9n.us}" 4242
```

Swap `STATUS` for any command. For multi-command probes, send each
as a separate invocation — not a persistent socket.

## ncat fallback

```sh
echo 'STATUS' | ncat --recv-only "${VOYAGER_HOST:-voyager1.v9n.us}" 4242
```

## Python fallback

Works anywhere Python is installed; no flavor detection.

```sh
python3 -c '
import socket, sys, os
host = os.environ.get("VOYAGER_HOST", "voyager1.v9n.us")
s = socket.create_connection((host, 4242), timeout=5)
s.sendall(b"STATUS\r\n")
buf = b""
s.settimeout(3)
try:
    while True:
        chunk = s.recv(4096)
        if not chunk: break
        buf += chunk
        if b"\n.\r\n" in buf or b"\n.\n" in buf: break
except socket.timeout: pass
s.close()
sys.stdout.write(buf.decode("ascii", errors="replace"))
'
```

## Node fallback

```sh
node -e '
const net = require("net");
const host = process.env.VOYAGER_HOST || "voyager1.v9n.us";
const s = net.connect(4242, host);
let buf = "";
s.on("connect", () => s.write("STATUS\r\n"));
s.on("data", d => {
  buf += d;
  if (/\n\.\r?\n/.test(buf)) { process.stdout.write(buf); s.end(); }
});
s.setTimeout(5000, () => { process.stdout.write(buf); s.destroy(); });
'
```

## PowerShell fallback (Windows only)

Use when the user is on Windows and has no WSL / Python / Node.

```powershell
$c = New-Object System.Net.Sockets.TcpClient("voyager1.v9n.us", 4242)
$c.ReceiveTimeout = 3000
$s = $c.GetStream()
$cmd = [System.Text.Encoding]::ASCII.GetBytes("STATUS`r`n")
$s.Write($cmd, 0, $cmd.Length)
$buf = New-Object System.IO.MemoryStream
$ch = New-Object byte[] 4096
try {
  while ($true) {
    $n = $s.Read($ch, 0, $ch.Length)
    if ($n -le 0) { break }
    $buf.Write($ch, 0, $n)
    $t = [System.Text.Encoding]::ASCII.GetString($buf.ToArray())
    if ($t -match "`n\.`r?`n") { break }
  }
} catch [System.IO.IOException] { }
$c.Close()
[System.Text.Encoding]::ASCII.GetString($buf.ToArray())
```

## Parsing rules

- Read until a line containing only `.` for multi-line replies.
- Read until timeout (short — 1-3s) for single-line replies /
  errors; there's no terminator on those.
- Stop on `?BUSY` / `?OVF` / `?TIMEOUT` / `?SHUTDOWN`; the server
  closes after sending.
- Strip CR/LF when comparing tokens. All server output is uppercase.

## Failure handling

| Symptom | Action |
|---|---|
| `nc: invalid option -- 'q'` | Re-detect flavor; use `-w 2` |
| Connection refused | Report to user; don't retry silently |
| `?BUSY` | Tell user the server is full; wait before retry |
| Empty output | Peer closed early; retry once, then report |
| Hang with no data | `nc` flavor mismatch or network; switch transport |
