Win32 Python Global Password Helper
===================================

Are you forced to use Microsoft Windows?

Are you forced to remember many shared passwords?

This app will help you.

This app register a Win32 global hot key (Ctrl+Alt+Shift+P).  When hot key is pressed, a GUI appears with a list of usernames.
Select a username, then the password is copied to the clipboard.  Now, you can easily paste (Ctrl+V) this password.

Getting Started
===============

1. Hack pw.json to add credentials (usernames and passwords)
1. Launch `python main.py pw.json`
1. Strike `Ctrl+Alt+Shift+P`
1. Select username.
   1. Hot tip: Up/down arrow keys work, and `Enter` will press `OK` button
1. Password is copied to clipboard
1. Use `Ctrl+V` to paste password into dialog
1. Profit!

System Requirements
===================

Python 3+

`pip install pywin32`
