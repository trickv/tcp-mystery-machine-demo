# Transports

How to talk to `voyager1.v9n.us:4242` from your own machine. Pick
the section that matches your OS. Open a socket, type commands at
the `> ` prompt, type `QUIT` when done.

**Don't want to fight your OS?** Open the bootcamp's GitHub
Codespace at
<https://github.com/trickv/coding-bootcamp-codespace> — it's a
Linux environment with `nc` and `telnet` already installed, in your
browser, free.

---

## macOS

```sh
telnet voyager1.v9n.us 4242
# or
nc voyager1.v9n.us 4242
```

Both ship with macOS. Works the same way interactively.

---

## Windows

Honestly, **just use the web terminal at
<https://voyager1.v9n.us/>**. It's identical in every way that
matters and it works in any browser. Windows doesn't ship `nc` or a
usable `telnet` and the alternatives involve enough PowerShell that
they're not worth it for a poking session.

If you really want a local client: install
[WSL](https://learn.microsoft.com/en-us/windows/wsl/install) and
use the Linux tools inside it:

```sh
wsl
telnet voyager1.v9n.us 4242
```

Or spin up the bootcamp [Codespace](https://github.com/trickv/coding-bootcamp-codespace)
and do it from the browser.

---

## Linux

```sh
telnet voyager1.v9n.us 4242
# or
nc voyager1.v9n.us 4242
```

If neither is installed, grab them on Debian / Ubuntu / WSL:

```sh
sudo apt install -y telnet netcat-openbsd
```

On Fedora / RHEL: `sudo dnf install telnet nmap-ncat` (then use
`ncat` in place of `nc`). On Arch: `sudo pacman -S inetutils
openbsd-netcat`.

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
| Connection refused | server down, wrong port, firewall | check host / port 4242 |
| Connection hangs with no banner | network firewall blocking TCP out | try from a different network |
| `?BUSY` received | server at 200-connection cap | retry later |
| `?TIMEOUT` and disconnect | you idled for 120s | reconnect |

---

## Last resort: programmatic fallbacks

If `telnet`, `nc`, and PowerShell all fail you and you still have
Python or Node on the box, these send one command and print the
response:

### Python

```sh
python3 -c '
import socket, sys
s = socket.create_connection(("voyager1.v9n.us", 4242), timeout=5)
s.sendall(b"STATUS\r\n")
s.settimeout(3)
buf = b""
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

### Node

```sh
node -e '
const net = require("net");
const s = net.connect(4242, "voyager1.v9n.us");
let buf = "";
s.on("connect", () => s.write("STATUS\r\n"));
s.on("data", d => {
  buf += d;
  if (/\n\.\r?\n/.test(buf)) { process.stdout.write(buf); s.end(); }
});
s.setTimeout(5000, () => { process.stdout.write(buf); s.destroy(); });
'
```
