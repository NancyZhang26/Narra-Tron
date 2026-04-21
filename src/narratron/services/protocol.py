from __future__ import annotations

import logging
import socket
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

TURN_PAGE_CMD = b"TURN_PAGE\n"


@dataclass(slots=True)
class TurnPageSignal:
    source: str
    reason: str
    timestamp_iso: str


class SoftwareProtocolBus:
    """Protocol bus that emits turn-page signals to a Raspberry Pi over TCP.

    Set pi_host to the Pi's IP/hostname to enable real transmission.
    When pi_host is empty the signal is logged only (useful for dev/mock).
    """

    def __init__(self, pi_host: str = "", pi_port: int = 9999) -> None:
        self.pi_host = pi_host
        self.pi_port = pi_port

    def emit_turn_page(self, source: str, reason: str) -> TurnPageSignal:
        signal = TurnPageSignal(
            source=source,
            reason=reason,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )
        if self.pi_host:
            self._send_to_pi(signal)
        else:
            logger.info(
                "TURN_PAGE signal emitted (no Pi host configured): %s",
                signal.timestamp_iso,
            )
        return signal

    def _send_to_pi(self, signal: TurnPageSignal) -> None:
        """Open a short-lived TCP connection and fire the turn-page command."""
        try:
            with socket.create_connection(
                (self.pi_host, self.pi_port), timeout=5
            ) as sock:
                sock.sendall(TURN_PAGE_CMD)
            logger.info(
                "TURN_PAGE sent to Pi at %s:%d at %s",
                self.pi_host,
                self.pi_port,
                signal.timestamp_iso,
            )
        except OSError as exc:
            # Log but don't crash — a missed page turn is recoverable.
            logger.error(
                "Failed to send TURN_PAGE to Pi at %s:%d: %s",
                self.pi_host,
                self.pi_port,
                exc,
            )
