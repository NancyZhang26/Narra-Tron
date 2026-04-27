"""Tests for SoftwareProtocolBus._send_to_pi() ACK handling."""
import socket
import threading

import pytest

from narratron.services.protocol import SoftwareProtocolBus


def _run_ack_server(host, port, response: bytes, delay: float = 0.0):
    """Minimal TCP server that accepts one connection, reads the command, sends response."""
    import time

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    srv.settimeout(5)
    conn, _ = srv.accept()
    conn.recv(64)  # consume TURN_PAGE\n
    if delay:
        time.sleep(delay)
    conn.sendall(response)
    conn.close()
    srv.close()


def _start_server(port, response: bytes, delay: float = 0.0):
    t = threading.Thread(target=_run_ack_server, args=("127.0.0.1", port, response, delay), daemon=True)
    t.start()
    return t


def test_send_to_pi_waits_for_ack():
    """emit_turn_page must not return until the ACK is received."""
    port = 19991
    _start_server(port, b"ACK\n")

    import time
    bus = SoftwareProtocolBus(pi_host="127.0.0.1", pi_port=port)
    t0 = time.monotonic()
    sig = bus.emit_turn_page(source="test", reason="unit test")
    elapsed = time.monotonic() - t0

    assert sig.source == "test"
    assert elapsed < 3.0  # should complete well within timeout


def test_send_to_pi_logs_warning_on_bad_ack(caplog):
    """A response that doesn't contain ACK should log a warning but not raise."""
    import logging
    port = 19992
    _start_server(port, b"UNKNOWN\n")

    bus = SoftwareProtocolBus(pi_host="127.0.0.1", pi_port=port)
    with caplog.at_level(logging.WARNING, logger="narratron.services.protocol"):
        bus.emit_turn_page(source="test", reason="bad ack test")

    assert any("ACK" in r.message for r in caplog.records)


def test_send_to_pi_logs_error_on_connection_refused(caplog):
    """A refused connection should log an error but not crash."""
    import logging
    # Port 19993 has no server running
    bus = SoftwareProtocolBus(pi_host="127.0.0.1", pi_port=19993)
    with caplog.at_level(logging.ERROR, logger="narratron.services.protocol"):
        bus.emit_turn_page(source="test", reason="no server")

    assert any("Failed" in r.message or "refused" in r.message.lower() for r in caplog.records)


def test_no_host_does_not_connect():
    """With pi_host='', emit_turn_page should not attempt a TCP connection."""
    bus = SoftwareProtocolBus(pi_host="")
    sig = bus.emit_turn_page(source="test", reason="mock mode")
    assert sig.source == "test"
