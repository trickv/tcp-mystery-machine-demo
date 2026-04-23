# Transports

Pick in priority order: `nc` → `ncat` → `python3` → `node`. Always one-shot
(send command, read until `.` terminator or quiet, close). Never hold a
socket open across turns.

Assume `$VOYAGER_HOST` is set; fall back to `voyager.example.com`.

## 1. `nc` (preferred)

Two common flavors with different flag sets. Detect first:

```sh
if nc -h 2>&1 | grep -q -- '-q'; then
  NC_ARGS="-q 1"          # OpenBSD nc (most Linux distros)
else
  NC_ARGS="-w 2"          # BSD nc (macOS default)
fi
echo 'STATUS' | nc $NC_ARGS "${VOYAGER_HOST:-voyager.example.com}" 4242
```

- **OpenBSD nc** (`netcat-openbsd` on Debian/Ubuntu): use `-q 1` — exit 1s after EOF on stdin. Without this, nc hangs waiting for the server to close.
- **BSD nc** (macOS): no `-q`. Use `-w 2` — 2-second idle timeout.
- **GNU netcat** (rare): use `-c` to close after stdin EOF.

## 2. `ncat` (nmap)

Different binary; always available where nmap is installed.

```sh
echo 'STATUS' | ncat --recv-only "${VOYAGER_HOST:-voyager.example.com}" 4242
```

`--recv-only` is the analog of OpenBSD `-q` — close send side after stdin EOF
and keep reading until the server closes.

## 3. `python3` one-liner (always works if Python is installed)

```sh
python3 -c '
import socket, sys, os
host = os.environ.get("VOYAGER_HOST", "voyager.example.com")
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
const host = process.env.VOYAGER_HOST || "voyager.example.com";
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
