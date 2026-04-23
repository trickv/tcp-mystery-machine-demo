# Transports

How to talk to `voyager1.v9n.us:4242` from your own machine. Pick the
section that matches your OS. Always use one-shot queries — don't hold
a socket open across commands.

If `VOYAGER_HOST` is set in your environment the examples use it;
otherwise they fall back to `voyager1.v9n.us`.

---

## Linux

Most distros ship OpenBSD `nc` (the `netcat-openbsd` package):

```sh
echo 'STATUS' | nc -q 1 voyager1.v9n.us 4242
```

The `-q 1` tells `nc` to exit one second after stdin closes; without
it, `nc` hangs waiting for the server to close the connection.

If `nc` isn't installed, `ncat` (part of `nmap`) works too:

```sh
echo 'STATUS' | ncat --recv-only voyager1.v9n.us 4242
```

---

## macOS

macOS ships BSD `nc`, which does **not** have `-q`. Use `-w 2`
instead (exit after 2 seconds of idle):

```sh
echo 'STATUS' | nc -w 2 voyager1.v9n.us 4242
```

If you don't know which `nc` you have, this detects and runs the
right one:

```sh
if nc -h 2>&1 | grep -q -- '-q'; then
  NC_ARGS="-q 1"          # OpenBSD (most Linux)
else
  NC_ARGS="-w 2"          # BSD (macOS)
fi
echo 'STATUS' | nc $NC_ARGS voyager1.v9n.us 4242
```

---

## Windows

Three options, easiest first.

### Option 1 — WSL

If you have WSL installed, use the Linux `nc` inside it:

```sh
wsl -- bash -c "echo STATUS | nc -q 1 voyager1.v9n.us 4242"
```

### Option 2 — PowerShell

Stock Win10/Win11, no install. `nc` isn't on Windows, but .NET has a
TCP client:

```powershell
$client = New-Object System.Net.Sockets.TcpClient("voyager1.v9n.us", 4242)
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
} catch [System.IO.IOException] { }
$client.Close()
[System.Text.Encoding]::ASCII.GetString($buf.ToArray())
```

Swap `"STATUS"` for any other command. `$host` is a reserved
PowerShell variable — don't use it.

### Option 3 — Don't use `telnet.exe`

It's disabled by default on modern Windows, can't reliably emit CRLF,
and can't detect the server's `.` end-of-reply. Use WSL or PowerShell.

---

## Interactive poking: `telnet`

Any OS, if `telnet` is installed:

```sh
telnet voyager1.v9n.us 4242
```

Type commands and press Enter. `QUIT` to exit cleanly, or Ctrl-] then
`quit` to force-close.

---

## Programmatic fallbacks

If nothing above works, these run anywhere the respective runtime is
installed.

### Python

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
        if b"\n.\r\n" in buf or b"\n.\n" in buf:
            break
except socket.timeout:
    pass
s.close()
sys.stdout.write(buf.decode("ascii", errors="replace"))
'
```

For multiple commands in one connection, separate with `\r\n`.

### Node

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

---

## How to read the replies

- **Banner on connect:** `VGR1 FDS READY` then a `> ` prompt.
- **Single-line reply:** one line, then `> ` again. All errors look
  like `?CMD`, `?SYNTAX`, `?BUSY`, `?OVF`, `?TIMEOUT`, `?SHUTDOWN`.
- **Multi-line reply:** several lines terminated by a line containing
  only `.` (SMTP-style). Stop reading when you see that line.
- **On `?BUSY` / `?OVF` / `?TIMEOUT` / `?SHUTDOWN`** the server closes
  the connection after sending the error.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `nc` hangs indefinitely | OpenBSD nc without `-q 1` | add `-q 1` |
| `nc: invalid option -- 'q'` | BSD/macOS nc | use `-w 2` instead |
| Connection refused | server down, wrong port, firewall | check host / port 4242 |
| `?BUSY` received | server at 200-connection cap | retry later |
| Empty output on a one-shot | peer closed before reply | very unlikely in practice |
