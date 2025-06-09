#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper script to run the Strands Agent with proper encoding support.
This script ensures proper handling of UTF-8 characters in input/output.
"""

import sys
import io
import locale
from main import main

# Set standard input/output encoding to UTF-8
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Print current encoding information
print(f"Default encoding: {sys.getdefaultencoding()}")
print(f"Locale encoding: {locale.getpreferredencoding()}")
print(f"Stdin encoding: {sys.stdin.encoding}")
print(f"Stdout encoding: {sys.stdout.encoding}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}")
        print("If you're experiencing encoding issues, try running the script with:")
        print("PYTHONIOENCODING=utf-8 python3 fix_encoding.py")
