import collections
import ctypes.wintypes
import dataclasses
import datetime
import io
import json
import os.path
import re
import sys
from typing import Optional, List, Dict, Any

import pywin.dialogs.list
import win32api
import win32clipboard
import win32con

APP_NAME = "Global Password Helper"
# Win32 Global Hot Key: Ctrl+Alt+Shift+P
HOT_KEY = "P"


def show_help_then_exit(*, error: Optional[str] = None) -> None:
    if error is not None:
        print(f"ERROR: {error}")

    print(f"Usage: {sys.argv[0]} JSON_CONFIG_FILE")
    print(APP_NAME)
    print(f"Registers Win32 global hot key (Ctrl+Alt+Shift+{HOT_KEY})")
    print("Press Win32 global hot key to display dialog with list of usernames (or descriptions)")
    print("Select username to copy password to clipboard")
    print("Ctrl+V to paste password from clipboard to system password dialog")
    print()
    print("Required Arguments:")
    print("    JSON_CONFIG_FILE: File path to JSON config")
    print("        Ex: C:\\src\\pw.json")
    sys.exit(1)


def read_nqjson_file(file_path: str) -> str:
    """
    :param file_path: path to file with "not quite" JSON (comments allowed)
    :return: file contents converted to valid JSON (comments removed)
    """
    with io.open(file=file_path, mode="r", encoding="utf-8") as fh:
        nqjson_list: List[str] = fh.readlines()

    json_line_list = nqjson_list.copy()

    regex: re.Pattern = re.compile("#.*$")

    for i in range(len(json_line_list)):
        line: str = json_line_list[i]
        adj_line = regex.sub("", line)
        json_line_list[i] = adj_line

    json_text: str = "".join(json_line_list)
    return json_text


def assert_no_dupe_username(config: Dict[str, Any]) -> None:
    c = collections.Counter([cdict["username"] for cdict in config["credential_list"]])
    dupe_username_list: List[str] = [username for username, count in c.items() if count > 1]
    if len(dupe_username_list) > 0:
        raise Exception(f"Duplicate username(s): {dupe_username_list}")


@dataclasses.dataclass
class Credential:
    # Ex: "username_xyz" or "some descriptive text for a secret"
    username: str
    password: str


def log(msg: str) -> None:
    print(f"{datetime.datetime.now()}: {msg}")


def hot_key_callback(cred_list: List[Credential]) -> None:
    username_list: List[str] = [c.username for c in cred_list]
    # Ref: https://stackoverflow.com/questions/68469243/dialog-box-to-select-option-from-list-in-python-on-windows
    dlg = pywin.dialogs.list.ListDialog(title=APP_NAME, list=username_list)
    index: Optional[int] = None
    if dlg.DoModal() == win32con.IDOK:
        index = dlg.selecteditem

    # index: Optional[int] = pywin.dialogs.list.SelectFromList("Copy password to clipboard for user:", username_list)
    if index is None:
        log("Win32 dialog cancelled with escape key -- do nothing")
        return

    cred: Credential = cred_list[index]

    # Ref: http://timgolden.me.uk/pywin32-docs/win32clipboard__SetClipboardText_meth.html
    # Many applications will want to call this function twice, with the same string specified but CF_UNICODETEXT specified the second.
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.SetClipboardText(cred.password, win32clipboard.CF_TEXT)
        win32clipboard.SetClipboardText(cred.password, win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()

    log(f"Win32 dialog selected username: {cred.username}: Password copied to clipboard")

    # win32api.MessageBox(None, f"Username [{cred.username}]: Copied password to clipboard", APP_NAME, win32con.MB_OK)


def main(argv: List[str]) -> None:
    print()
    if 2 != len(argv):
        show_help_then_exit(error="Missing requirement argument: JSON_CONFIG_FILE")
    elif argv[0] in ["/?", "-h", "--help"]:
        show_help_then_exit()

    config_file_path: str = argv[1]
    config_file_abs_path: str = os.path.abspath(config_file_path)
    json_text: str = read_nqjson_file(config_file_abs_path)
    config: Dict[str, Any] = json.loads(json_text)
    assert_no_dupe_username(config)
    cred_list: List[Credential] = [Credential(cdict["username"], cdict["password"]) for cdict in config["credential_list"]]

    # Ref: https://stackoverflow.com/questions/74703948/pywin-dialogs-list-listdialog-unexpected-focus-when-called-after-global-hot-key
    win32api.MessageBox(None,
                        (f"Loaded {len(cred_list)} credentials from {config_file_abs_path}"
                         + f"\n\nGlobal hot key: Ctrl+Alt+Shift+{HOT_KEY}")
                        , APP_NAME, win32con.MB_OK)

    # Ref: https://gist.github.com/m10x/a9a2eb296fab2106a5ae7c16b8874a4b
    hot_key_index = 0
    if not ctypes.windll.user32.RegisterHotKey(None,
                                               hot_key_index,
                                               win32con.MOD_ALT + win32con.MOD_CONTROL + win32con.MOD_SHIFT,
                                               ord(HOT_KEY)):
        raise Exception("Failed: user32.RegisterHotKey()")

    try:
        msg = ctypes.wintypes.MSG()
        while ctypes.windll.user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == win32con.WM_HOTKEY:
                if hot_key_index == msg.wParam:
                    hot_key_callback(cred_list)

            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageA(ctypes.byref(msg))
    finally:
        ctypes.windll.user32.UnregisterHotKey(None, hot_key_index)


if __name__ == "__main__":
    main(sys.argv)
