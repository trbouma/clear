#!/usr/bin/env python
"""Compatibility wrapper for `clear-lab redeem`."""

from __future__ import annotations

import sys

from clear.lab_cli import main

if __name__ == "__main__":
    sys.argv.insert(1, "redeem")
    raise SystemExit(main())
