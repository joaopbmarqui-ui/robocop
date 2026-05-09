#!/usr/bin/env python3
"""Small SMTP catcher for Dispatch development mode."""

import asyncore
import smtpd
import sys
import time
from pathlib import Path


class FileMailbox(smtpd.SMTPServer):
    def __init__(self, localaddr, remoteaddr, output_dir: Path):
        super().__init__(localaddr, remoteaddr)
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        timestamp = time.strftime("%Y%m%dT%H%M%S")
        path = self.output_dir / f"{timestamp}_{len(list(self.output_dir.glob('*.eml'))):04d}.eml"
        if isinstance(data, bytes):
            payload = data
        else:
            payload = data.encode("utf-8", errors="replace")
        path.write_bytes(payload)
        print(f"captured email {path} from={mailfrom} to={','.join(rcpttos)}", flush=True)
        return None


def main() -> int:
    root = Path(__file__).resolve().parent
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "sent_emails"
    FileMailbox(("127.0.0.1", 2525), None, output_dir)
    print(f"mock SMTP listening on 127.0.0.1:2525; writing to {output_dir}", flush=True)
    asyncore.loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
