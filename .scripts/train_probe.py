#!/usr/bin/env python3
"""
train_probe.py -- diagnose tethered-cellular connectivity (the "train problem").

WHAT IT DOES
  Runs a protocol ladder against a fixed host (1.1.1.1) every few seconds, while
  cycling a 2x2 experiment:

      TTL   64 (native)  vs  65  -- 65 defeats carrier tethering detection,
                                     because the phone decrements it back to 64
      MTU 1500 (default) vs 1400 -- 1400 defeats a path-MTU blackhole

  Conditions rotate every PHASE_SECS, so position along the track is balanced
  across all four cells: cell congestion and handovers average out instead of
  masquerading as an effect.

  The ladder is the diagnosis. Same destination IP, ascending demands:

      icmp_small   ICMP, tiny                  -- is the path up at all?
      icmp_1500/1400/1260  ICMP, DF, sized     -- what is the real path MTU?
      dns_udp      UDP:53, small               -- does UDP work?
      dns_tcp      TCP:53, small response      -- does TCP work at all?
      dns_tls      TCP:853, TLS (big cert)     -- do LARGE inbound TCP packets work?
      http_plain   TCP:80, tiny response       -- real-world TCP, no TLS
      https_tcp    TCP:443 + TLS               -- real-world TCP + TLS
      bulk         TCP:443, 256 KB             -- sustained TCP

  dns_tcp OK but dns_tls hanging, to the SAME IP, is an MTU blackhole.
  dns_udp OK but dns_tcp hanging is TCP shaping/blocking. Those are different
  problems with different fixes, and this separates them.

USAGE
  sudo python3 ~/.scripts/train_probe.py run     # Ctrl-C to stop; report opens
  python3 ~/.scripts/train_probe.py report FILE.jsonl

  While running, type any text + Enter to log an annotation ("tunnel", "toggled
  radio", "passing Hadera"). Try NOT to toggle the radio -- it resets the very
  state we're measuring -- but if you must, annotate it.

  Without sudo it still runs, but only observes (no TTL/MTU arms).
"""

import json
import os
import re
import select
import signal
import socket
import ssl
import struct
import subprocess
import sys
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------- configuration

TARGET_IP = "1.1.1.1"           # the fixed host for the protocol ladder
TARGET_DOT_SNI = "cloudflare-dns.com"
HTTP_PLAIN_URL = "http://captive.apple.com/hotspot-detect.html"   # tiny, no TLS
HTTPS_URL = "https://www.google.com/generate_204"                 # tiny, TLS
BULK_URL = "https://speed.cloudflare.com/__down?bytes=262144"     # 256 KB

TICK_SECS = int(os.environ.get("TRAIN_TICK", 10))    # one full ladder every N sec
PHASE_SECS = int(os.environ.get("TRAIN_PHASE", 120))  # how long each condition holds
BULK_EVERY = 6                  # run the bulk download every Nth tick
STATE_EVERY = 3                 # sample tailscale/adb every Nth tick
PROBE_TIMEOUT = 8               # per-probe hard timeout (seconds)

def build_phases(mtu_arm, native_mtu):
    """The experiment grid. Falls back to a TTL-only A/B when the MTU arm can't
    run safely -- which is the normal case on Wi-Fi (see valid_mtu_range)."""
    grid = [
        {"name": "A", "ttl": 64, "mtu": native_mtu},   # baseline: today
        {"name": "B", "ttl": 65, "mtu": native_mtu},   # tethering-detection counter
    ]
    if mtu_arm:
        grid += [
            {"name": "C", "ttl": 64, "mtu": MTU_LOW},  # MTU-blackhole counter
            {"name": "D", "ttl": 65, "mtu": MTU_LOW},  # both
        ]
    return grid

# ICMP payload sizes -> total IP packet size is payload + 28.
ICMP_SIZES = {"icmp_1500": 1472, "icmp_1400": 1372, "icmp_1260": 1232}

OUTDIR = Path.home() / "train-probe"

# ------------------------------------------------------------------- primitives


def run(cmd, timeout=PROBE_TIMEOUT):
    """Run a command, never raise. Returns (rc, stdout, stderr)."""
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as exc:  # noqa: BLE001
        return 125, "", str(exc)


def default_iface():
    rc, out, _ = run(["route", "-n", "get", "default"], timeout=4)
    if rc == 0:
        m = re.search(r"interface:\s*(\S+)", out)
        if m:
            return m.group(1)
    return "en0"


def service_for_iface(iface):
    """Map a BSD device (en0) to a networksetup service name ("Wi-Fi")."""
    rc, out, _ = run(["networksetup", "-listnetworkserviceorder"], timeout=6)
    if rc != 0:
        return None
    m = re.search(r"\(Hardware Port: ([^,]+), Device: " + re.escape(iface) + r"\)", out)
    return m.group(1) if m else None


def valid_mtu_range(iface):
    """The MTU range macOS will actually ACCEPT for this interface.

    This is the whole ballgame. Wi-Fi reports a *default* MTU of 1500 but a
    settable range of only 1280-1436 -- so lowering it succeeds and raising it
    back to 1500 fails, permanently stranding the interface. Read this before
    touching anything.
    """
    svc = service_for_iface(iface)
    if not svc:
        return None
    rc, out, _ = run(["networksetup", "-listvalidMTUrange", svc], timeout=6)
    if rc != 0:
        return None
    m = re.search(r"(\d+)\s*-\s*(\d+)", out)
    return (int(m.group(1)), int(m.group(2))) if m else None


def iface_info(iface):
    rc, out, _ = run(["ifconfig", iface], timeout=4)
    if rc != 0:
        return {"mtu": None, "v4": None, "has_v6": False}
    mtu = re.search(r"mtu (\d+)", out)
    v4 = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", out)
    # a routable v6 address (not link-local fe80::)
    has_v6 = bool(re.search(r"inet6 (?!fe80)[0-9a-f:]+", out))
    return {
        "mtu": int(mtu.group(1)) if mtu else None,
        "v4": v4.group(1) if v4 else None,
        "has_v6": has_v6,
    }


# ------------------------------------------------------------------ the probes


def probe_icmp(size):
    """ICMP echo with Don't-Fragment at a given payload size.

    If the local interface MTU is already below the packet size, the kernel
    refuses to send it -- that is not a network failure, so mark it distinctly.
    """
    t0 = time.time()
    rc, out, err = run(
        ["ping", "-c", "1", "-W", "2500", "-D", "-s", str(size), TARGET_IP],
        timeout=6,
    )
    elapsed_ms = (time.time() - t0) * 1000
    blob = (out + " " + err).lower()
    if "message too long" in blob or "too big" in blob:
        return {"status": "n/a", "ms": None}      # can't leave the host; not a result
    if rc == 0:
        m = re.search(r"time=([\d.]+) ms", out)
        return {"status": "ok", "ms": float(m.group(1)) if m else elapsed_ms}
    return {"status": "fail", "ms": None}


def _dns_query(qname="example.com", qtype=1):
    txid = os.urandom(2)
    header = txid + struct.pack(">HHHHH", 0x0100, 1, 0, 0, 0)
    q = b"".join(
        bytes([len(part)]) + part.encode() for part in qname.split(".")
    ) + b"\x00" + struct.pack(">HH", qtype, 1)
    return txid, header + q


def probe_dns_udp():
    txid, pkt = _dns_query()
    t0 = time.time()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(4)
    try:
        s.sendto(pkt, (TARGET_IP, 53))
        data, _ = s.recvfrom(2048)
        if data[:2] != txid:
            return {"status": "fail", "ms": None}
        return {"status": "ok", "ms": (time.time() - t0) * 1000}
    except Exception:  # noqa: BLE001
        return {"status": "fail", "ms": None}
    finally:
        s.close()


def probe_dns_tcp():
    """Small request, small response, over TCP. Isolates 'does TCP work'."""
    txid, pkt = _dns_query()
    framed = struct.pack(">H", len(pkt)) + pkt
    t0 = time.time()
    try:
        s = socket.create_connection((TARGET_IP, 53), timeout=5)
        t_conn = (time.time() - t0) * 1000
        s.settimeout(5)
        s.sendall(framed)
        head = s.recv(2)
        if len(head) < 2:
            s.close()
            return {"status": "fail", "ms": None, "t_connect": t_conn}
        s.close()
        return {
            "status": "ok",
            "ms": (time.time() - t0) * 1000,
            "t_connect": t_conn,
        }
    except Exception:  # noqa: BLE001
        return {"status": "fail", "ms": None, "t_connect": None}


def probe_dns_tls():
    """TCP connect, then a TLS handshake -- whose server response (certificate
    chain) is several KB, i.e. the first genuinely LARGE inbound packets.

    Same IP as probe_dns_tcp. If TCP succeeds here and TLS hangs, big inbound
    packets are being dropped: a path-MTU blackhole, not a blocked port.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE   # we're testing packet flow, not trust
    t0 = time.time()
    try:
        raw = socket.create_connection((TARGET_IP, 853), timeout=5)
        t_conn = (time.time() - t0) * 1000
    except Exception:  # noqa: BLE001
        return {"status": "fail", "phase": "connect", "t_connect": None,
                "t_handshake": None}
    try:
        raw.settimeout(6)
        t1 = time.time()
        tls = ctx.wrap_socket(raw, server_hostname=TARGET_DOT_SNI)
        t_hs = (time.time() - t1) * 1000
        tls.close()
        return {"status": "ok", "phase": "done", "t_connect": t_conn,
                "t_handshake": t_hs}
    except Exception:  # noqa: BLE001
        try:
            raw.close()
        except Exception:  # noqa: BLE001
            pass
        # TCP came up but the handshake didn't complete -> the smoking gun.
        return {"status": "fail", "phase": "handshake", "t_connect": t_conn,
                "t_handshake": None}


_persist = {"sock": None, "since": None}


def probe_tcp_persist():
    """A LONG-LIVED TCP connection, held open and reused across ticks.

    THE discriminator. When new TCP is dying, this asks the follow-up question:
    does an ALREADY-ESTABLISHED flow keep working?

      established survives + new TCP fails  -> connection SETUP is being blocked
                                               (CGNAT port exhaustion, or SYNs
                                               dropped). Existing flows are fine.
      established dies too                  -> something is actively tearing down
                                               TCP mid-stream (DPI/RST injection).

    Those have different fixes, so this is worth a dedicated socket.
    """
    out = {"established_ok": None, "new_ok": None, "age": None}
    s = _persist["sock"]
    if s is not None:
        try:
            s.settimeout(6)
            s.sendall(b"GET /cdn-cgi/trace HTTP/1.1\r\nHost: 1.1.1.1\r\n"
                      b"Connection: keep-alive\r\n\r\n")
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = s.recv(4096)
                if not chunk:
                    raise ConnectionError("closed")
                buf += chunk
            out["established_ok"] = True
            out["age"] = time.time() - _persist["since"]
            out["status"] = "ok"
            return out
        except Exception:  # noqa: BLE001
            try:
                s.close()
            except Exception:  # noqa: BLE001
                pass
            _persist["sock"] = None
            out["established_ok"] = False   # the established flow DIED

    # No live connection (first tick, or it just died). Can we make a new one?
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        raw = socket.create_connection((TARGET_IP, 443), timeout=6)
        tls = ctx.wrap_socket(raw, server_hostname="one.one.one.one")
        _persist["sock"] = tls
        _persist["since"] = time.time()
        out["new_ok"] = True
        out["age"] = 0.0
        out["status"] = "ok"
    except Exception:  # noqa: BLE001
        out["new_ok"] = False
        out["status"] = "fail"
    return out


CURL_FMT = "%{http_code} %{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total} %{speed_download}"


def probe_curl(url, ipv=4, max_time=PROBE_TIMEOUT):
    rc, out, _ = run(
        ["curl", f"-{ipv}", "-s", "-o", "/dev/null", "--max-time", str(max_time),
         "-w", CURL_FMT, url],
        timeout=max_time + 3,
    )
    if rc != 0 or not out:
        return {"status": "fail", "rc": rc}
    parts = out.split()
    if len(parts) < 6:
        return {"status": "fail", "rc": rc}
    code, t_conn, t_app, t_first, t_total, speed = parts
    ok = code.startswith("2") or code.startswith("3")
    return {
        "status": "ok" if ok else "fail",
        "http_code": int(code),
        "t_connect": float(t_conn) * 1000,
        "t_appconnect": float(t_app) * 1000,   # TLS handshake done
        "t_firstbyte": float(t_first) * 1000,
        "t_total": float(t_total) * 1000,
        "kbps": float(speed) / 1024,
    }


# --------------------------------------------------------------- local machine


def sample_sockets():
    rc, out, _ = run(["netstat", "-an", "-p", "tcp"], timeout=6)
    est = out.count("ESTABLISHED") if rc == 0 else None
    rc2, out2, _ = run(["netstat", "-an", "-p", "udp"], timeout=6)
    udp = (len(out2.splitlines()) - 2) if rc2 == 0 else None
    return {"tcp_established": est, "udp_sockets": udp}


def sample_tailscale():
    rc, out, _ = run(["tailscale", "status", "--json"], timeout=5)
    if rc != 0:
        return {"state": "unknown", "peers": None}
    try:
        d = json.loads(out)
        peers = d.get("Peer") or {}
        return {"state": d.get("BackendState", "?"), "peers": len(peers)}
    except Exception:  # noqa: BLE001
        return {"state": "unknown", "peers": None}


_adb_failures = [0]


def sample_adb():
    """Best-effort phone radio telemetry. Only works if USB-connected."""
    if _adb_failures[0] >= 3:
        return None
    rc, out, _ = run(
        ["adb", "shell", "dumpsys telephony.registry | grep -m2 -E "
         "'mSignalStrength=|mTelephonyDisplayInfo='"],
        timeout=6,
    )
    if rc != 0 or not out:
        _adb_failures[0] += 1
        return None
    _adb_failures[0] = 0
    rsrp = re.search(r"rsrp=(-?\d+)", out)
    nettype = re.search(r"network=(\w+)", out) or re.search(r"overrideNetworkType=(\w+)", out)
    return {
        "rsrp": int(rsrp.group(1)) if rsrp else None,
        "net": nettype.group(1) if nettype else None,
    }


# ------------------------------------------------------------ experiment knobs


MTU_LOW = 1400   # the clamped condition


class Knobs:
    """Applies and restores the TTL / MTU experiment conditions.

    Hard-won rule: NEVER lower an MTU we cannot provably raise again. macOS will
    happily accept a one-way change on Wi-Fi and strand the interface below its
    default until you bounce the radio. So the MTU arm is gated on a read-only
    capability check up front, and is either fully on or never touched.
    """

    def __init__(self, iface):
        self.iface = iface
        self.root = os.geteuid() == 0
        self.orig_ttl = self._get_ttl()
        self.orig_mtu = iface_info(iface)["mtu"]
        self.mtu_arm = False
        self.mtu_skip_reason = None
        self.applied = {"ttl": self.orig_ttl, "mtu": self.orig_mtu}

        if not self.root:
            self.mtu_skip_reason = "not root"
        else:
            self._decide_mtu_arm()

    def _decide_mtu_arm(self):
        rng = valid_mtu_range(self.iface)
        if not rng:
            self.mtu_skip_reason = (
                f"macOS won't report a valid MTU range for {self.iface}")
            return
        lo, hi = rng
        if self.orig_mtu is None:
            self.mtu_skip_reason = "could not read the current MTU"
            return
        # We must be able to get BACK to orig_mtu, and get DOWN to MTU_LOW.
        if not (lo <= self.orig_mtu <= hi):
            self.mtu_skip_reason = (
                f"current MTU {self.orig_mtu} is outside the settable range "
                f"{lo}-{hi}, so it could not be restored (this is the Wi-Fi case)")
            return
        if not (lo <= MTU_LOW <= hi):
            self.mtu_skip_reason = (
                f"MTU {MTU_LOW} is outside the settable range {lo}-{hi}")
            return
        self.mtu_arm = True

    def _get_ttl(self):
        rc, out, _ = run(["sysctl", "-n", "net.inet.ip.ttl"], timeout=3)
        return int(out) if rc == 0 and out.isdigit() else 64

    def _set_mtu(self, mtu):
        run(["ifconfig", self.iface, "mtu", str(mtu)], timeout=4)
        return iface_info(self.iface)["mtu"] == mtu

    def apply(self, ttl, mtu):
        if not self.root:
            return
        if ttl != self.applied.get("ttl"):
            run(["sysctl", "-w", f"net.inet.ip.ttl={ttl}"], timeout=4)
            run(["sysctl", "-w", f"net.inet6.ip6.hlim={ttl}"], timeout=4)
            self.applied["ttl"] = ttl
        if self.mtu_arm and mtu != self.applied.get("mtu"):
            if self._set_mtu(mtu):
                self.applied["mtu"] = mtu
            else:
                # Pre-flighted, so this should be unreachable -- but if it ever
                # happens, get back to a known-good MTU rather than limping on.
                print(f"  ! MTU {mtu} refused unexpectedly; restoring and "
                      f"disabling the MTU arm.")
                self.mtu_arm = False
                self._restore_mtu()

    def _restore_mtu(self):
        """Restore the original MTU. Returns True only if it VERIFIABLY took.

        There is deliberately no clever escalation here. On Wi-Fi, once the MTU
        is below the default, neither ifconfig nor a radio power-cycle can raise
        it back (tested 2026-07-14) -- so there is no recovery to attempt, only
        an honest report. The real protection is _decide_mtu_arm(), which never
        lowers an MTU it cannot provably raise.
        """
        if not self.orig_mtu or iface_info(self.iface)["mtu"] == self.orig_mtu:
            return True
        return self._set_mtu(self.orig_mtu)

    def restore(self):
        if not self.root:
            return
        run(["sysctl", "-w", f"net.inet.ip.ttl={self.orig_ttl}"], timeout=4)
        run(["sysctl", "-w", f"net.inet6.ip6.hlim={self.orig_ttl}"], timeout=4)
        ttl_ok = self._get_ttl() == self.orig_ttl
        mtu_ok = self._restore_mtu()
        now = iface_info(self.iface)["mtu"]
        if ttl_ok and mtu_ok:
            print("\n  network settings restored "
                  f"(ttl {self.orig_ttl}, mtu {now}).")
        else:
            # Never again claim success without checking.
            print("\n  !! COULD NOT FULLY RESTORE NETWORK SETTINGS !!")
            if not ttl_ok:
                print(f"     ttl is {self._get_ttl()}, expected {self.orig_ttl}")
                print(f"     fix: sudo sysctl -w net.inet.ip.ttl={self.orig_ttl}")
            if not mtu_ok:
                print(f"     {self.iface} mtu is {now}, expected {self.orig_mtu}")
                print(f"     try: sudo ifconfig {self.iface} mtu {self.orig_mtu}")
                print(f"     if that is refused, the driver must re-attach:")
                print(f"       sudo ifconfig {self.iface} down && "
                      f"sudo ifconfig {self.iface} up")
                print(f"     and if it still will not take, a reboot will reset it.")


# ------------------------------------------------------------------- the runner


def glyph(status):
    return {"ok": "\033[32m+\033[0m", "fail": "\033[31mX\033[0m",
            "n/a": "\033[90m.\033[0m"}.get(status, "?")


def one_tick(do_bulk, do_state):
    """Fire the whole ladder concurrently; return a flat result dict."""
    out = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {
            "icmp_small": ex.submit(probe_icmp, 56),
            "dns_udp": ex.submit(probe_dns_udp),
            "dns_tcp": ex.submit(probe_dns_tcp),
            "dns_tls": ex.submit(probe_dns_tls),
            "http_plain": ex.submit(probe_curl, HTTP_PLAIN_URL, 4, 8),
            "https_tcp": ex.submit(probe_curl, HTTPS_URL, 4, 8),
            "tcp_persist": ex.submit(probe_tcp_persist),
        }
        for name, size in ICMP_SIZES.items():
            futs[name] = ex.submit(probe_icmp, size)
        if do_bulk:
            futs["bulk"] = ex.submit(probe_curl, BULK_URL, 4, 12)
        if do_state:
            futs["_sockets"] = ex.submit(sample_sockets)
            futs["_tailscale"] = ex.submit(sample_tailscale)
            futs["_adb"] = ex.submit(sample_adb)

        for name, fut in futs.items():
            try:
                out[name] = fut.result(timeout=PROBE_TIMEOUT + 8)
            except Exception:  # noqa: BLE001
                out[name] = {"status": "fail", "error": "probe crashed"}
    return out


def cmd_run():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    logfile = OUTDIR / f"train_{stamp}.jsonl"

    iface = default_iface()
    info = iface_info(iface)
    knobs = Knobs(iface)

    phases = build_phases(knobs.mtu_arm, knobs.orig_mtu)

    print(f"\n  train_probe -- iface {iface}  ip {info['v4']}  mtu {info['mtu']}"
          f"  v6 {'yes' if info['has_v6'] else 'no'}")
    if not knobs.root:
        print("  ! not root: OBSERVE-ONLY (no TTL arm). Re-run with sudo for "
              "the full experiment.")
    elif knobs.mtu_arm:
        print(f"  experiment: TTL 64/65 x MTU {knobs.orig_mtu}/{MTU_LOW}, "
              f"rotating every {PHASE_SECS}s")
    else:
        print(f"  experiment: TTL 64/65, rotating every {PHASE_SECS}s")
        print(f"  ! MTU arm OFF -- {knobs.mtu_skip_reason}.")
        print(f"    The MTU is left untouched, so the ICMP ladder still measures "
              f"the path MTU\n    directly (that is the actual diagnostic).")
    if (info["mtu"] or 0) < 1500:
        print(f"\n  !! {iface} MTU is {info['mtu']}, not the default 1500.")
        print(f"     The 1500-byte ICMP probe CANNOT RUN -- the kernel rejects it")
        print(f"     locally -- so the path-MTU measurement, the single most")
        print(f"     important thing this tool does, will be missing.")
        print(f"     If a previous run left it low:  sudo ifconfig {iface} mtu 1500")
        print(f"     (or turn Wi-Fi off and on again), then re-run.")
        print(f"     Continuing in 10s -- Ctrl-C now if that's not intended.\n")
        time.sleep(10)

    print(f"  log: {logfile}")
    print("  type a note + Enter to annotate. Ctrl-C to stop and see the report.\n")

    stop = {"now": False}
    stdin_live = {"ok": sys.stdin is not None and sys.stdin.isatty()}

    def on_sigint(_sig, _frm):
        stop["now"] = True

    signal.signal(signal.SIGINT, on_sigint)

    t_start = time.time()
    tick = 0
    fh = logfile.open("a")
    try:
        while not stop["now"]:
            tick += 1
            tick_start = time.time()
            elapsed = tick_start - t_start
            # Assign the condition by TICK INDEX, never by wall-clock. Failures
            # come in multi-minute EPISODES; if a tick runs long (probes timing
            # out) a clock-keyed schedule clumps conditions into runs, and the
            # episode boundaries then masquerade as a condition effect. Keying
            # off the tick index guarantees every N consecutive ticks covers all
            # N conditions no matter how long each one takes.
            phase = phases[(tick - 1) % len(phases)]
            knobs.apply(phase["ttl"], phase["mtu"])
            mtu_now = iface_info(iface)["mtu"]

            res = one_tick(
                do_bulk=(tick % BULK_EVERY == 1),
                do_state=(tick % STATE_EVERY == 1),
            )

            rec = {
                "t": time.time(),
                "elapsed": round(elapsed, 1),
                "phase": phase["name"],
                "ttl": knobs.applied.get("ttl"),
                "mtu": mtu_now,
                "mtu_arm": knobs.mtu_arm,
                "native_mtu": knobs.orig_mtu,
                "probes": res,
            }
            fh.write(json.dumps(rec) + "\n")
            fh.flush()

            def g(k):
                return glyph((res.get(k) or {}).get("status", "?"))

            sock = res.get("_sockets") or {}
            est = sock.get("tcp_established")
            icmp_ms = (res.get("icmp_small") or {}).get("ms")
            line = (
                f"  {datetime.now():%H:%M:%S} {phase['name']} "
                f"ttl{rec['ttl']} mtu{mtu_now} | "
                f"icmp {g('icmp_small')}{f'{icmp_ms:5.0f}ms' if icmp_ms else '      '} "
                f"1500{g('icmp_1500')} 1400{g('icmp_1400')} 1260{g('icmp_1260')} | "
                f"udp{g('dns_udp')} tcp{g('dns_tcp')} tls{g('dns_tls')} | "
                f"http{g('http_plain')} https{g('https_tcp')}"
                + (f" | est {est}" if est is not None else "")
            )
            print(line)

            def drain_notes():
                """Consume any typed annotations. MUST run every tick, not only
                while idling -- when probes hang, a tick overruns its budget and
                there is no idle time left, and notes typed during it were being
                silently dropped."""
                if not stdin_live["ok"]:
                    return
                while True:
                    r, _, _ = select.select([sys.stdin], [], [], 0)
                    if not r:
                        return
                    note = sys.stdin.readline()
                    if note == "":       # EOF -- stdin closed, stop polling it
                        stdin_live["ok"] = False
                        return
                    note = note.strip()
                    if not note:
                        continue
                    fh.write(json.dumps(
                        {"t": time.time(), "elapsed": round(time.time() - t_start, 1),
                         "annotation": note}) + "\n")
                    fh.flush()
                    print(f"      ^ noted: {note}")

            drain_notes()
            # Pace from when THIS tick began, so a slow tick doesn't cause the
            # loop to spin trying to catch up on a schedule it can never meet.
            deadline = tick_start + TICK_SECS
            while time.time() < deadline and not stop["now"]:
                time.sleep(min(0.3, max(0.0, deadline - time.time())))
                drain_notes()
    finally:
        fh.close()
        knobs.restore()   # prints its own verified success/failure report

    print(f"  {tick} samples -> {logfile}\n")
    build_report(logfile)

    # Running under sudo makes the outputs root-owned, which then breaks a
    # plain `train_probe.py report` re-run. Hand them back to the real user.
    uid, gid = os.environ.get("SUDO_UID"), os.environ.get("SUDO_GID")
    if uid and gid:
        for p in (logfile, logfile.with_suffix(".html")):
            try:
                os.chown(p, int(uid), int(gid))
            except OSError:
                pass


# ---------------------------------------------------------------------- report

LADDER = [
    ("icmp_small", "ICMP small", "is the path up at all?"),
    ("icmp_1500", "ICMP @1500", "does a full-size packet survive?"),
    ("icmp_1400", "ICMP @1400", "does a 1400-byte packet survive?"),
    ("icmp_1260", "ICMP @1260", "does a small packet survive?"),
    ("dns_udp", "DNS / UDP", "does UDP work?"),
    ("dns_tcp", "DNS / TCP", "does TCP work at all? (small response)"),
    ("dns_tls", "DNS / TLS", "do LARGE inbound TCP packets work?"),
    ("http_plain", "HTTP (TCP)", "real-world TCP, no TLS"),
    ("https_tcp", "HTTPS (TCP+TLS)", "real-world TCP + TLS"),
    ("bulk", "Bulk 256KB (TCP)", "sustained TCP throughput"),
    ("tcp_persist", "TCP (long-lived)", "does an ALREADY-OPEN connection survive?"),
]

TCP_PROBES = ["dns_tcp", "dns_tls", "http_plain", "https_tcp", "bulk"]


def load(logfile):
    rows, notes = [], []
    for line in Path(logfile).read_text().splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        (notes if "annotation" in d else rows).append(d)
    return rows, notes


def rate(rows, key, predicate=None):
    """Success rate for a probe over rows matching predicate. 'n/a' excluded."""
    ok = tot = 0
    for r in rows:
        if predicate and not predicate(r):
            continue
        p = (r.get("probes") or {}).get(key)
        if not p or p.get("status") == "n/a":
            continue
        tot += 1
        if p.get("status") == "ok":
            ok += 1
    return (ok / tot if tot else None), tot


def diagnose(rows):
    """Turn the ladder + the 2x2 into ranked, evidence-backed conclusions."""
    findings = []

    def r(key, pred=None):
        v, n = rate(rows, key, pred)
        return (v, n)

    mtu_native = lambda x: x.get("mtu") != MTU_LOW    # noqa: E731
    mtu_low = lambda x: x.get("mtu") == MTU_LOW       # noqa: E731
    ttl64 = lambda x: x.get("ttl") == 64              # noqa: E731
    ttl65 = lambda x: x.get("ttl") == 65              # noqa: E731

    # -- 0. Did the 1500-byte probe actually get to run? If the interface MTU
    #       is below 1500 the kernel drops it locally and we learn nothing --
    #       say so loudly rather than reporting a silent pile of n/a.
    _, n1500 = r("icmp_1500")
    if n1500 < max(5, len(rows) * 0.2):
        native = next((x.get("native_mtu") for x in rows if x.get("native_mtu")), None)
        findings.append((
            60, "warning",
            "The 1500-byte probe could not run -- path MTU is UNMEASURED.",
            f"Only {n1500} of {len(rows)} samples managed to send a full-size "
            f"packet; the interface MTU ({native}) was below 1500, so the kernel "
            f"rejected them locally. This is a gap in the data, not a result.",
            "Re-run with the interface at its native 1500 MTU.",
        ))

    # -- 1. Is the path MTU below 1500?  (only meaningful at native MTU)
    big, nb = r("icmp_1500", mtu_native)
    small, ns = r("icmp_1260", mtu_native)
    if big is not None and small is not None and nb >= 5 and ns >= 5:
        if small - big > 0.30:
            findings.append((
                90, "critical",
                "Path MTU is below 1500 -- full-size packets are being dropped.",
                f"1500-byte ICMP succeeded {big:.0%} of the time while 1260-byte "
                f"ICMP succeeded {small:.0%}, to the same host. The link claims "
                f"1500 but cannot carry it.",
                "Clamp the Mac's interface MTU: `sudo ifconfig {IFACE} mtu 1400` "
                "(try 1280 if 1400 isn't enough).",
            ))
        elif big > 0.8:
            findings.append((
                20, "good",
                "Path MTU is fine at 1500.",
                f"Full-size 1500-byte ICMP succeeded {big:.0%} of the time. "
                "A path-MTU blackhole is NOT your problem.",
                "No MTU change needed.",
            ))

    # -- 2. TCP-large vs TCP-small, same IP. The MTU smoking gun.
    tcp, nt = r("dns_tcp")
    tls, nl = r("dns_tls")
    if tcp is not None and tls is not None and nt >= 5 and nl >= 5:
        if tcp - tls > 0.30:
            findings.append((
                85, "critical",
                "Large inbound TCP packets are being blackholed (MTU, not blocking).",
                f"To the SAME IP: small-response DNS-over-TCP succeeded {tcp:.0%}, "
                f"but DNS-over-TLS -- whose only difference is a multi-kilobyte "
                f"certificate coming back -- succeeded {tls:.0%}. The port is open; "
                f"the big packets vanish. That is a classic PMTUD blackhole and it "
                f"is exactly why TCP+TLS hangs while QUIC (which self-limits to "
                f"~1200 bytes) sails through.",
                "Clamp the MTU on the Mac's tethering interface.",
            ))

    # -- 3. TCP vs UDP. If TCP dies where UDP lives, it's shaping, not MTU.
    udp, nu = r("dns_udp")
    if udp is not None and tcp is not None and nu >= 5 and nt >= 5:
        if udp - tcp > 0.30:
            findings.append((
                80, "critical",
                "TCP itself is being dropped while UDP flows freely.",
                f"To the same IP: UDP succeeded {udp:.0%}, TCP succeeded {tcp:.0%} "
                f"-- and TCP is failing even on a tiny response, so this is not a "
                f"packet-size problem. Something is discriminating against TCP: "
                f"carrier shaping, tethering enforcement, or a middlebox.",
                "See the TTL result below -- that tells you if it's tethering detection.",
            ))

    # -- 4. THE TTL ARM. Aggregate every TCP probe -- an earlier version keyed
    #       off whichever single probe answered first and drew the wrong
    #       conclusion from a noisy one.
    def tcp_rate(pred):
        ok = tot = 0
        for x in rows:
            if not pred(x):
                continue
            for k in TCP_PROBES:
                p = (x.get("probes") or {}).get(k)
                if p and p.get("status") in ("ok", "fail"):
                    tot += 1
                    ok += p["status"] == "ok"
        return (ok / tot if tot else None), tot

    a, na = tcp_rate(ttl64)
    b, nb2 = tcp_rate(ttl65)
    if a is not None and b is not None and na >= 20 and nb2 >= 20:
        if b - a > 0.20:
            findings.append((
                95, "critical",
                "The TTL hack works -- the carrier is fingerprinting your hop count.",
                f"Across all TCP probes: {a:.0%} success at TTL 64 (packets leave "
                f"the phone at 63, betraying that they were forwarded) vs {b:.0%} "
                f"at TTL 65 (they leave at 64, looking phone-originated).",
                "FIX: `sudo sysctl -w net.inet.ip.ttl=65` and "
                "`sudo sysctl -w net.inet6.ip6.hlim=65` on the Mac.",
            ))
        else:
            findings.append((
                40, "good",
                "The TTL countermeasure does NOT work.",
                f"Across all TCP probes: {a:.0%} at TTL 64 vs {b:.0%} at TTL 65 "
                f"({na} and {nb2} probes). Raising the TTL does not rescue TCP, so "
                f"hop-count is not the discriminator. NOTE: this does not clear "
                f"tethering enforcement in general -- a carrier can fingerprint the "
                f"TCP stack itself, which TTL games will not fool.",
                "Don't bother with the TTL hack; test a UDP tunnel instead.",
            ))

    # -- 5. THE MTU ARM: does clamping actually fix it? (only if it ran)
    if any(x.get("mtu_arm") for x in rows):
        for probe, nice in (("https_tcp", "HTTPS"), ("dns_tls", "DNS/TLS")):
            a, na = r(probe, mtu_native)
            b, nb2 = r(probe, mtu_low)
            if a is None or b is None or na < 5 or nb2 < 5:
                continue
            if b - a > 0.20:
                findings.append((
                    92, "critical",
                    "CONFIRMED: clamping the MTU fixes it.",
                    f"{nice} succeeded {a:.0%} at the native MTU but {b:.0%} at "
                    f"MTU {MTU_LOW}. Same route, same conditions -- only the "
                    f"packet size changed.",
                    f"PERMANENT FIX: clamp the MTU to {MTU_LOW} whenever you "
                    f"tether. Worth wiring into a 'commute mode' script.",
                ))
                break

    # -- 6. WHERE does TCP die: at connection SETUP, or mid-stream?
    #       dns_tcp records t_connect, so a failure with no t_connect means the
    #       3-way handshake never completed -- the SYN went nowhere.
    blocked = [x for x in rows
               if (x["probes"].get("dns_udp") or {}).get("status") == "ok"
               and (x["probes"].get("dns_tcp") or {}).get("status") == "fail"]
    if len(blocked) >= 10:
        no_syn = sum(1 for x in blocked
                     if (x["probes"].get("dns_tcp") or {}).get("t_connect") is None)
        frac = no_syn / len(blocked)
        findings.append((
            88, "critical",
            "TCP is dying at connection SETUP, while UDP and ICMP are fine.",
            f"In {len(blocked)} blocked samples, the TCP handshake failed to "
            f"complete {frac:.0%} of the time -- the SYN never gets a reply. This "
            f"is not throttling and not a packet-size problem: new TCP connections "
            f"simply cannot be established, while UDP to the same IP works.",
            "See the long-lived-connection result -- that says whether it is "
            "CGNAT port exhaustion or active blocking.",
        ))

        # -- 7. THE DISCRIMINATOR: do ALREADY-OPEN TCP connections survive?
        surv = [x["probes"]["tcp_persist"].get("established_ok") for x in blocked
                if x["probes"].get("tcp_persist")]
        surv = [s for s in surv if s is not None]
        if len(surv) >= 5:
            alive = sum(1 for s in surv if s) / len(surv)
            if alive > 0.7:
                # New UDP flows are created every tick by dns_udp. If those also
                # succeed during the block, the carrier NAT has spare capacity --
                # so this is NOT port exhaustion (which would starve UDP too), it
                # is a TCP-SYN-selective filter: tethering enforcement.
                udp_new, _ = r("dns_udp", lambda x: x in blocked)
                if udp_new is not None and udp_new > 0.6:
                    findings.append((
                        94, "critical",
                        "New TCP is being FILTERED at the SYN -- tethering "
                        "enforcement, not NAT exhaustion.",
                        f"During the block: new TCP connections failed but "
                        f"already-open ones survived {alive:.0%}, AND brand-new "
                        f"UDP flows still succeeded {udp_new:.0%}. If the carrier "
                        f"NAT were out of ports, new UDP would fail too -- it "
                        f"doesn't. So capacity is fine; something specifically "
                        f"drops NEW TCP SYNs while leaving UDP and established TCP "
                        f"alone. That is a tethering/DPI policy filter. Cutting the "
                        f"Mac's connection count will NOT help -- the filter blocks "
                        f"new TCP regardless of how many you have.",
                        "TUNNEL OVER UDP -- a Tailscale exit node (`commute-mode "
                        "on`). All TCP then rides inside one WireGuard/UDP flow the "
                        "filter can't see. This is the fix.",
                    ))
                else:
                    findings.append((
                        93, "critical",
                        "Established TCP survives, new TCP fails -- likely NAT/CGNAT "
                        "port-block exhaustion.",
                        f"A long-lived TCP connection kept working through "
                        f"{alive:.0%} of the blocked samples while new connections "
                        f"failed, and new UDP flows were also struggling -- "
                        f"consistent with the carrier NAT running out of port "
                        f"mappings.",
                        "Cut the Mac's connection churn (`tailscale down`, quit "
                        "Syncthing), then tunnel over UDP (`commute-mode on`), which "
                        "collapses hundreds of flows into ONE.",
                    ))
            elif alive < 0.3:
                findings.append((
                    93, "critical",
                    "Even ESTABLISHED TCP connections are being killed.",
                    f"A long-lived TCP connection survived only {alive:.0%} of the "
                    f"blocked samples. Existing flows are being torn down, not just "
                    f"new ones -- that is active interference (DPI / RST injection), "
                    f"not port exhaustion.",
                    "Tunnel everything over UDP (a WireGuard/Tailscale exit node) so "
                    "the carrier cannot see or touch your TCP at all.",
                ))

    # -- 7. Nothing broke.
    h, nh = r("https_tcp")
    if h is not None and h > 0.95 and nh >= 20 and not [f for f in findings if f[0] > 50]:
        findings.append((
            5, "good",
            "Nothing failed during this run.",
            f"HTTPS succeeded {h:.0%} of {nh} attempts. The problem did not "
            f"reproduce -- run again on a bad ride.",
            "Re-run when it's actually misbehaving.",
        ))

    findings.sort(key=lambda f: -f[0])
    return findings


# ------------------------------------------------------------------ HTML report

HTML_TMPL = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Train connectivity probe &mdash; __STAMP__</title>
<style>
  :root {
    color-scheme: light dark;
    --surface-1:#fcfcfb; --plane:#f9f9f7;
    --text-primary:#0b0b0b; --text-secondary:#52514e; --muted:#898781;
    --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,0.10);
    --good:#0ca30c; --warning:#fab219; --serious:#ec835a; --critical:#d03b3b;
    --s1:#2a78d6; --s2:#1baf7a; --s3:#eda100; --s5:#4a3aa7;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --surface-1:#1a1a19; --plane:#0d0d0d;
      --text-primary:#fff; --text-secondary:#c3c2b7; --muted:#898781;
      --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10);
      --s1:#3987e5; --s2:#199e70; --s3:#c98500; --s5:#9085e9;
    }
  }
  * { box-sizing:border-box; }
  body {
    margin:0; padding:32px 24px 64px; background:var(--plane);
    color:var(--text-primary);
    font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
  }
  .wrap { max-width:1100px; margin:0 auto; }
  h1 { font-size:24px; margin:0 0 4px; letter-spacing:-0.01em; }
  .sub { color:var(--text-secondary); margin:0 0 32px; font-size:14px; }
  .card {
    background:var(--surface-1); border:1px solid var(--border);
    border-radius:10px; padding:20px 22px; margin-bottom:20px;
  }
  h2 { font-size:13px; text-transform:uppercase; letter-spacing:0.07em;
       color:var(--muted); margin:0 0 16px; font-weight:600; }
  .finding { display:flex; gap:14px; padding:14px 0; border-top:1px solid var(--grid); }
  .finding:first-of-type { border-top:none; padding-top:0; }
  .dot { flex:0 0 auto; width:10px; height:10px; border-radius:50%; margin-top:6px; }
  .finding h3 { margin:0 0 5px; font-size:16px; font-weight:600; letter-spacing:-0.005em; }
  .finding p { margin:0 0 8px; color:var(--text-secondary); font-size:14px; }
  .fix { font-size:13.5px; color:var(--text-primary); }
  .fix b { font-weight:600; }
  code { font:13px ui-monospace,SFMono-Regular,Menlo,monospace;
         background:var(--plane); border:1px solid var(--border);
         padding:1.5px 5px; border-radius:4px; }
  .scroll { overflow-x:auto; }
  table { border-collapse:collapse; width:100%; font-size:13.5px;
          font-variant-numeric:tabular-nums; }
  th,td { text-align:right; padding:7px 12px; border-bottom:1px solid var(--grid);
          white-space:nowrap; }
  th:first-child, td:first-child { text-align:left; }
  th { color:var(--muted); font-weight:600; font-size:12px;
       text-transform:uppercase; letter-spacing:0.05em; }
  td.q { color:var(--text-secondary); font-size:12.5px; text-align:left;
         white-space:normal; }
  .legend { display:flex; gap:18px; flex-wrap:wrap; margin-bottom:14px;
            font-size:13px; color:var(--text-secondary); }
  .legend span { display:inline-flex; align-items:center; gap:7px; }
  .sw { width:12px; height:12px; border-radius:3px; display:inline-block; }
  .tip {
    position:fixed; pointer-events:none; opacity:0; transition:opacity .1s;
    background:var(--surface-1); border:1px solid var(--border);
    border-radius:7px; padding:8px 11px; font-size:12.5px;
    box-shadow:0 4px 16px rgba(0,0,0,.16); z-index:99; max-width:280px;
  }
  .tip b { display:block; margin-bottom:3px; font-size:13px; }
  .hint { color:var(--muted); font-size:12.5px; margin:12px 0 0; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Train connectivity probe</h1>
  <p class="sub">__STAMP__ &middot; __NSAMP__ samples over __DUR__ &middot; interface __IFACE__</p>

  <div class="card">
    <h2>Verdict</h2>
    __FINDINGS__
  </div>

  <div class="card">
    <h2>The protocol ladder &mdash; where does it break?</h2>
    <div class="scroll"><table>
      <thead><tr>
        <th>Probe</th><th>What it answers</th><th>Success</th><th>n</th>
        <th>TTL 64</th><th>TTL 65</th><th>MTU native</th><th>MTU __MTULOW__</th>
      </tr></thead>
      <tbody>__LADDER__</tbody>
    </table></div>
    <p class="hint">Read top to bottom. The first row that collapses is where your
      connection dies &mdash; and the rows above it tell you what still works.</p>
  </div>

  <div class="card">
    <h2>Timeline &mdash; every probe, every tick</h2>
    <div class="legend">
      <span><i class="sw" style="background:var(--good)"></i> pass</span>
      <span><i class="sw" style="background:var(--critical)"></i> fail</span>
      <span><i class="sw" style="background:var(--grid)"></i> n/a</span>
      <span style="margin-left:auto;color:var(--muted)">bands above = experiment condition</span>
    </div>
    <div class="scroll"><div id="strip"></div></div>
  </div>

  <div class="card">
    <h2>ICMP round-trip time</h2>
    <div class="scroll"><div id="rtt"></div></div>
  </div>

  <div class="card">
    <h2>Open TCP sockets on the Mac <span style="text-transform:none;font-weight:400">(the NAT-exhaustion check)</span></h2>
    <div class="scroll"><div id="sock"></div></div>
  </div>
</div>
<div class="tip" id="tip"></div>
<script>
const DATA = __DATA__;
const tip = document.getElementById('tip');
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const NS = 'http://www.w3.org/2000/svg';
const el = (n, a={}) => { const e = document.createElementNS(NS, n);
  for (const k in a) e.setAttribute(k, a[k]); return e; };

function showTip(e, html) {
  tip.innerHTML = html; tip.style.opacity = 1;
  const x = Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 12);
  tip.style.left = x + 'px';
  tip.style.top = Math.max(8, e.clientY - tip.offsetHeight - 12) + 'px';
}
const hideTip = () => { tip.style.opacity = 0; };

const fmtT = s => {
  const m = Math.floor(s / 60), r = Math.round(s % 60);
  return m + ':' + String(r).padStart(2, '0');
};

/* ---------- strip chart: rows = probes, columns = ticks ---------- */
function strip() {
  const rows = DATA.ladder, ticks = DATA.rows;
  const LEFT = 132, TOP = 34, CH = 22, GAP = 2;
  const cw = Math.max(5, Math.min(14, 820 / Math.max(ticks.length, 1)));
  const W = LEFT + ticks.length * cw + 16;
  const H = TOP + rows.length * CH + 34;
  const svg = el('svg', {width: W, height: H, viewBox: `0 0 ${W} ${H}`});

  // defs: a hatch so failure is not encoded by colour alone
  const defs = el('defs');
  const p = el('pattern', {id:'hatch', width:5, height:5,
    patternUnits:'userSpaceOnUse', patternTransform:'rotate(45)'});
  p.appendChild(el('rect', {width:5, height:5, fill:'transparent'}));
  const ln = el('line', {x1:0, y1:0, x2:0, y2:5,
    stroke:'rgba(255,255,255,.55)', 'stroke-width':2});
  p.appendChild(ln); defs.appendChild(p); svg.appendChild(defs);

  // condition band
  const bandColor = {A: css('--grid'), B: css('--s1'), C: css('--s3'), D: css('--s5')};
  ticks.forEach((t, i) => {
    const r = el('rect', {x: LEFT + i*cw, y: 12, width: Math.max(1, cw - GAP/2),
      height: 8, rx: 2, fill: bandColor[t.phase] || css('--grid'), opacity: .75});
    r.addEventListener('mousemove', e => showTip(e,
      `<b>${fmtT(t.elapsed)}</b>Condition ${t.phase} &mdash; TTL ${t.ttl}, MTU ${t.mtu}`));
    r.addEventListener('mouseleave', hideTip);
    svg.appendChild(r);
  });

  rows.forEach((row, ri) => {
    const y = TOP + ri * CH;
    const lbl = el('text', {x: LEFT - 10, y: y + CH/2 + 4, 'text-anchor': 'end',
      fill: css('--text-secondary'), 'font-size': 12});
    lbl.textContent = row.label;
    svg.appendChild(lbl);

    ticks.forEach((t, i) => {
      const st = (t.probes[row.key] || {}).status || 'n/a';
      const fill = st === 'ok' ? css('--good')
                 : st === 'fail' ? css('--critical') : css('--grid');
      const g = el('g');
      const rect = el('rect', {x: LEFT + i*cw, y: y + 2, rx: 2,
        width: Math.max(1, cw - GAP), height: CH - 6, fill,
        opacity: st === 'n/a' ? .5 : .92});
      g.appendChild(rect);
      if (st === 'fail' && cw >= 5) {
        g.appendChild(el('rect', {x: LEFT + i*cw, y: y + 2, rx: 2,
          width: Math.max(1, cw - GAP), height: CH - 6, fill: 'url(#hatch)'}));
      }
      const hit = el('rect', {x: LEFT + i*cw - 3, y: y, width: cw + 6,
        height: CH, fill: 'transparent'});
      hit.addEventListener('mousemove', e => showTip(e,
        `<b>${row.label} &mdash; ${st.toUpperCase()}</b>` +
        `t+${fmtT(t.elapsed)} &middot; condition ${t.phase} (TTL ${t.ttl}, MTU ${t.mtu})`));
      hit.addEventListener('mouseleave', hideTip);
      g.appendChild(hit);
      svg.appendChild(g);
    });
  });

  // x axis
  const ax = el('line', {x1: LEFT, y1: H - 26, x2: LEFT + ticks.length*cw,
    y2: H - 26, stroke: css('--axis'), 'stroke-width': 1});
  svg.appendChild(ax);
  // space labels by pixels, not by index -- otherwise they collide at small cw
  const labelEvery = Math.max(1, Math.ceil(58 / cw));
  ticks.forEach((t, i) => {
    if (i % labelEvery) return;
    const tx = el('text', {x: LEFT + i*cw, y: H - 10, fill: css('--muted'),
      'font-size': 11, 'text-anchor': 'middle'});
    tx.textContent = fmtT(t.elapsed);
    svg.appendChild(tx);
  });

  // annotations
  DATA.notes.forEach(n => {
    const i = ticks.findIndex(t => t.elapsed >= n.elapsed);
    if (i < 0) return;
    const x = LEFT + i * cw;
    svg.appendChild(el('line', {x1: x, y1: 24, x2: x, y2: H - 26,
      stroke: css('--serious'), 'stroke-width': 2, opacity: .85}));
    const m = el('circle', {cx: x, cy: 24, r: 4, fill: css('--serious')});
    m.addEventListener('mousemove', e => showTip(e, `<b>${fmtT(n.elapsed)}</b>${n.annotation}`));
    m.addEventListener('mouseleave', hideTip);
    svg.appendChild(m);
  });

  document.getElementById('strip').appendChild(svg);
}

/* ---------- single-series line chart ---------- */
function line(mount, series, unit, color) {
  const pts = series.filter(p => p.v != null);
  const W = 900, H = 200, L = 56, R = 14, T = 30, B = 30;
  const svg = el('svg', {width: W, height: H, viewBox: `0 0 ${W} ${H}`});
  if (!pts.length) {
    const t = el('text', {x: L, y: H/2, fill: css('--muted'), 'font-size': 13});
    t.textContent = 'no data';
    svg.appendChild(t); mount.appendChild(svg); return;
  }
  const xs = series.map(p => p.t);
  const x0 = Math.min(...xs), x1 = Math.max(...xs) || 1;

  // A line chart plots a LEVEL, so it needn't sit on zero -- and forcing zero
  // flattens a series like socket count whose variation is the whole point.
  // Zoom in when the spread is small relative to the level; else keep zero.
  const lo = Math.min(...pts.map(p => p.v)), hi = Math.max(...pts.map(p => p.v));
  const zoom = lo > 0 && (hi - lo) < lo * 0.6;
  const pad = (hi - lo) * 0.25 || Math.max(hi * 0.1, 1);
  const yMin = zoom ? Math.max(0, lo - pad) : 0;
  const yMax = (zoom ? hi + pad : hi * 1.15) || 1;

  const X = v => L + (v - x0) / (x1 - x0 || 1) * (W - L - R);
  const Y = v => H - B - ((v - yMin) / (yMax - yMin || 1)) * (H - T - B);

  for (let i = 0; i <= 4; i++) {
    const v = yMin + (yMax - yMin) * i / 4;
    svg.appendChild(el('line', {x1: L, y1: Y(v), x2: W - R, y2: Y(v),
      stroke: css('--grid'), 'stroke-width': 1}));
    const t = el('text', {x: L - 9, y: Y(v) + 4, 'text-anchor': 'end',
      fill: css('--muted'), 'font-size': 11});
    t.textContent = Math.round(v);
    svg.appendChild(t);
  }
  // unit sits above the plot, clear of the topmost tick label
  const t0 = el('text', {x: 6, y: 14, fill: css('--muted'), 'font-size': 11});
  t0.textContent = unit + (zoom ? '  (axis zoomed)' : '');
  svg.appendChild(t0);

  // break the path wherever data is missing, so gaps read as gaps
  let d = '', pen = false;
  series.forEach(p => {
    if (p.v == null) { pen = false; return; }
    d += (pen ? 'L' : 'M') + X(p.t) + ' ' + Y(p.v) + ' ';
    pen = true;
  });
  svg.appendChild(el('path', {d, fill: 'none', stroke: color,
    'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round'}));

  pts.forEach(p => {
    const c = el('circle', {cx: X(p.t), cy: Y(p.v), r: 3.5, fill: color,
      stroke: css('--surface-1'), 'stroke-width': 2});
    const hit = el('circle', {cx: X(p.t), cy: Y(p.v), r: 12, fill: 'transparent'});
    hit.addEventListener('mousemove', e => showTip(e,
      `<b>${Math.round(p.v)} ${unit}</b>t+${fmtT(p.t)}`));
    hit.addEventListener('mouseleave', hideTip);
    svg.appendChild(c); svg.appendChild(hit);
  });

  svg.appendChild(el('line', {x1: L, y1: H - B, x2: W - R, y2: H - B,
    stroke: css('--axis'), 'stroke-width': 1}));
  for (let i = 0; i <= 6; i++) {
    const v = x0 + (x1 - x0) * i / 6;
    const t = el('text', {x: X(v), y: H - 10, 'text-anchor': 'middle',
      fill: css('--muted'), 'font-size': 11});
    t.textContent = fmtT(v);
    svg.appendChild(t);
  }
  mount.appendChild(svg);
}

strip();
line(document.getElementById('rtt'),
  DATA.rows.map(r => ({t: r.elapsed, v: (r.probes.icmp_small || {}).ms ?? null})),
  'ms', css('--s1'));
line(document.getElementById('sock'),
  DATA.rows.filter(r => r.probes._sockets)
           .map(r => ({t: r.elapsed, v: r.probes._sockets.tcp_established ?? null})),
  'sockets', css('--s2'));
</script>
</body>
</html>
"""


def build_report(logfile):
    rows, notes = load(logfile)
    if not rows:
        print("  no samples in log; nothing to report.")
        return

    iface = default_iface()
    findings = diagnose(rows)

    # ---- terminal summary (so it's useful even without a browser)
    print("\n" + "=" * 74)
    print("  VERDICT")
    print("=" * 74)
    if not findings:
        print("\n  Not enough data to conclude. Run for longer (aim for 20+ min).\n")
    for _, sev, title, detail, fix in findings:
        mark = {"critical": "!!", "warning": " !", "good": " +"}.get(sev, "  ")
        print(f"\n  {mark}  {title}")
        for chunk in _wrap(detail, 66):
            print(f"      {chunk}")
        print(f"      -> {fix.replace('{IFACE}', iface)}")
    print("\n" + "-" * 74)
    print(f"  {'probe':<18}{'success':>9}{'n':>5}   {'ttl64':>6}{'ttl65':>7}"
          f"{'mtu-nat':>9}{f'mtu{MTU_LOW}':>9}")
    print("-" * 74)

    def pct(v):
        return "  -  " if v is None else f"{v * 100:3.0f}%"

    ladder_html = []
    for key, label, question in LADDER:
        v, n = rate(rows, key)
        if n == 0:
            continue
        a, _ = rate(rows, key, lambda x: x.get("ttl") == 64)
        b, _ = rate(rows, key, lambda x: x.get("ttl") == 65)
        c, _ = rate(rows, key, lambda x: x.get("mtu") != MTU_LOW)
        d, _ = rate(rows, key, lambda x: x.get("mtu") == MTU_LOW)
        print(f"  {label:<18}{pct(v):>9}{n:>5}   {pct(a):>6}{pct(b):>7}"
              f"{pct(c):>9}{pct(d):>9}")
        colour = ("var(--good)" if (v or 0) > 0.9
                  else "var(--critical)" if (v or 0) < 0.5 else "var(--warning)")
        ladder_html.append(
            f"<tr><td><b>{label}</b></td><td class='q'>{question}</td>"
            f"<td style='color:{colour};font-weight:600'>{pct(v).strip()}</td>"
            f"<td>{n}</td><td>{pct(a).strip()}</td><td>{pct(b).strip()}</td>"
            f"<td>{pct(c).strip()}</td><td>{pct(d).strip()}</td></tr>"
        )
    print("-" * 74 + "\n")

    # ---- html
    findings_html = []
    for _, sev, title, detail, fix in findings:
        findings_html.append(
            f"<div class='finding'><div class='dot' style='background:var(--{sev})'></div>"
            f"<div><h3>{title}</h3><p>{detail}</p>"
            f"<div class='fix'><b>Fix:</b> {_codeify(fix.replace('{IFACE}', iface))}</div>"
            f"</div></div>"
        )
    if not findings_html:
        findings_html.append(
            "<div class='finding'><div class='dot' style='background:var(--warning)'>"
            "</div><div><h3>Not enough data to conclude</h3><p>Run for at least 20 "
            "minutes, ideally while the problem is actually happening.</p></div></div>"
        )

    payload = {
        "rows": [
            {"elapsed": r["elapsed"], "phase": r.get("phase"), "ttl": r.get("ttl"),
             "mtu": r.get("mtu"), "probes": r.get("probes", {})}
            for r in rows
        ],
        "notes": notes,
        "ladder": [{"key": k, "label": l} for k, l, _ in LADDER
                   if rate(rows, k)[1] > 0],
    }
    dur = rows[-1]["elapsed"] - rows[0]["elapsed"]
    html = (HTML_TMPL
            .replace("__DATA__", json.dumps(payload))
            .replace("__FINDINGS__", "\n".join(findings_html))
            .replace("__LADDER__", "\n".join(ladder_html))
            .replace("__NSAMP__", str(len(rows)))
            .replace("__DUR__", f"{dur / 60:.0f} min")
            .replace("__IFACE__", iface)
            .replace("__MTULOW__", str(MTU_LOW))
            .replace("__STAMP__", Path(logfile).stem.replace("train_", "")))

    out = Path(logfile).with_suffix(".html")
    out.write_text(html)
    print(f"  report: {out}\n")
    try:
        webbrowser.open(f"file://{out}")
    except Exception:  # noqa: BLE001
        pass


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


def _codeify(text):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", text)


# -------------------------------------------------------------------------- cli

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("run", "report"):
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "run":
        cmd_run()
    else:
        if len(sys.argv) < 3:
            logs = sorted(OUTDIR.glob("train_*.jsonl"))
            if not logs:
                print("no logs in", OUTDIR)
                sys.exit(1)
            build_report(logs[-1])
        else:
            build_report(sys.argv[2])


if __name__ == "__main__":
    main()
