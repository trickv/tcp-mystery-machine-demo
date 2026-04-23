# Transports

Pick in priority order: `nc` → `ncat` → `python3` → `node`. Always one-shot
(send command, read until `.` terminator or quiet, close). Never hold a
socket open across turns.

Assume `$VOYAGER_HOST` is set; fall back to `voyager1.v9n.us`.

## 1. `nc` (preferred)

Two common flavors with different flag sets. Detect first:

```sh
if nc -h 2>&1 | grep -q -- '-q'; then
  NC_ARGS="-q 1"          # OpenBSD nc (most Linux distros)
else
  NC_ARGS="-w 2"          # BSD nc (macOS default)
fi
echo 'STATUS' | nc $NC_ARGS "${VOYAGER_HOST:-voyager1.v9n.us}" 4242
```

- **OpenBSD nc** (`netcat-openbsd` on Debian/Ubuntu): use `-q 1` — exit 1s after EOF on stdin. Without this, nc hangs waiting for the server to close.
- **BSD nc** (macOS): no `-q`. Use `-w 2` — 2-second idle timeout.
- **GNU netcat** (rare): use `-c` to close after stdin EOF.

## 2. `ncat` (nmap)

Different binary; always available where nmap is installed.

```sh
echo 'STATUS' | ncat --recv-only "${VOYAGER_HOST:-voyager1.v9n.us}" 4242
```

`--recv-only` is the analog of OpenBSD `-q` — close send side after stdin EOF
and keep reading until the server closes.

## 3. `python3` one-liner (always works if Python is installed)

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
        if not chunk:
            break
        buf += chunk
        # End on dot-line (multi-line reply) or after a prompt (single-line)
        if b"\n.\r\n" in buf or b"\n.\n" in buf:
            break
except socket.timeout:
    pass
s.close()
sys.stdout.write(buf.decode("ascii", errors="replace"))
'
```

Swap `b"STATUS\r\n"` for whatever command you want. For multiple commands in
one connection, separate with `\r\n`.

## 4. `node` one-liner

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
s.on("close", () => {});
'
```

## Windows

**Prefer WSL if available** — it gives the student a real `nc` and matches
every other example in this file:

```sh
wsl -- bash -c "echo STATUS | nc -q 1 \$VOYAGER_HOST 4242"
```

**PowerShell (stock Win10/11, no install):** use `System.Net.Sockets.TcpClient`
with raw byte reads (mirrors the Python one-liner — reads until the `\n.\r\n`
sentinel or the socket goes quiet).

```powershell
$Target = if ($env:VOYAGER_HOST) { $env:VOYAGER_HOST } else { "voyager1.v9n.us" }
$client = New-Object System.Net.Sockets.TcpClient($Target, 4242)
$client.ReceiveTimeout = 3000
$stream = $client.GetStream()
$cmd = [System.Text.Encoding]::ASCII.GetBytes("STATUS`r`n")
$stream.Write($cmd, 0, $cmd.Length)
$buf = New-Object System.IO.MemoryStream
$chunk = New-Object byte[] 4096
try {
  while ($true) {
    $n = $stream.Read($chunk, 0, $chunk.Length)
    if ($n -le 0) { break }
    $buf.Write($chunk, 0, $n)
    $text = [System.Text.Encoding]::ASCII.GetString($buf.ToArray())
    if ($text -match "`n\.`r?`n") { break }
  }
} catch [System.IO.IOException] {
  # ReceiveTimeout fired — use whatever we have (single-line replies like ?CMD)
}
$client.Close()
[System.Text.Encoding]::ASCII.GetString($buf.ToArray())
```

Gotchas:
- `$host` is a reserved PowerShell variable — use `$Target` (as above) or similar.
- Backtick-r backtick-n (`` `r`n ``) is PowerShell's CRLF escape.
- `ReceiveTimeout = 3000` makes `Stream.Read` throw `IOException` after 3s of
  silence, which is how we exit for single-line replies (`?CMD`, `?SYNTAX`,
  `?BUSY`) that have no `.` terminator. The `try/catch` treats that as
  "done, print what we have."
- Replace `"STATUS"` with any other command verbatim.

**cmd.exe:** no native TCP client. Don't use classic `telnet.exe` — it's
disabled by default, can't reliably send CRLF, and has no way to detect the
`.` terminator. If stuck on cmd, invoke PowerShell:

```cmd
powershell -NoProfile -Command "..."
```

**Git Bash:** does not ship `nc`. Use the PowerShell approach above, or
install Python and use the Python one-liner from section 3.

## Parsing hints

- Server banner arrives before your command is echoed as part of the reply. Typical first output: `VGR1 FDS READY\r\n> ` then your reply.
- For multi-line replies, stop reading when you see a line containing only `.`.
- Error codes (`?CMD`, `?SYNTAX`, `?BUSY`, `?OVF`, `?TIMEOUT`) are single lines — no dot terminator.
- On `?BUSY`, `?OVF`, `?TIMEOUT`, the server closes the connection after the reply.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `nc` hangs indefinitely | used OpenBSD nc without `-q 1` | add `-q 1` |
| `nc: invalid option -- 'q'` | BSD/macOS nc | use `-w 2` instead |
| Connection refused | server down, wrong port, firewall | check `$VOYAGER_HOST` / port 4242 |
| `?BUSY` received | server at 200-connection cap | retry later |
| Empty output | peer closed before reply | check server logs; shouldn't happen for one-shots |
