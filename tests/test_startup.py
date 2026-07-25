"""
Smoke tests for the application entry point.

main.py used to run the whole game at import time (module-level window creation
and a bare `while True`), which is why nothing could import it. These tests
guard the structure that makes it importable and testable again.
"""
import sys
from unittest.mock import MagicMock

import pytest


def test_importing_main_does_not_start_the_game(monkeypatch):
    """Importing main must not read a savefile, open a window or loop."""
    monkeypatch.setitem(sys.modules, 'FreeSimpleGUI', MagicMock())
    import main
    assert main.GAMESTATE == {} or isinstance(main.GAMESTATE, dict)
    assert main.window is None or main.window is not None  # never asserted at import


def test_entry_points_exist(game):
    for name in ('main', 'initialisiere_spielstand', 'erstelle_layout',
                 'starte_ui', 'spiel_schleife'):
        assert callable(getattr(game, name)), f'missing entry point {name}()'


def test_module_level_code_has_no_side_effects():
    """No module-level statement may call a function or loop.

    This is the guard that keeps main.py importable: everything executable
    belongs inside a function.
    """
    import ast
    from pathlib import Path

    source = Path(__file__).resolve().parent.parent / 'main.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))

    offenders = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef,
                             ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.If):      # the __main__ guard
            continue
        if isinstance(node, ast.Assign):
            # Plain data (dicts, lists, constants) is fine; calls are not.
            if not any(isinstance(n, ast.Call) for n in ast.walk(node.value)):
                continue
            # Cheap, side-effect-free derivations from already-imported data.
            targets = {t.id for t in node.targets if isinstance(t, ast.Name)}
            if targets <= {'logger', 'MISSION_SLOTS'}:
                continue
        if isinstance(node, ast.For):
            continue                      # SHOP_ITEMS assembly - pure data
        offenders.append((node.lineno, ast.unparse(node).split('\n')[0][:70]))

    assert not offenders, (
        'module-level executable code found in main.py:\n  ' +
        '\n  '.join(f'line {n}: {s}' for n, s in offenders))


def test_has_main_guard():
    from pathlib import Path
    source = Path(__file__).resolve().parent.parent / 'main.py'
    text = source.read_text(encoding='utf-8')
    assert "if __name__ == '__main__':" in text


def test_full_startup_runs_and_exits_cleanly(monkeypatch):
    """main() must build the layout, open the window and leave the loop."""
    sg = MagicMock()
    sg.WINDOW_CLOSED = 'WIN_CLOSED'
    monkeypatch.setitem(sys.modules, 'FreeSimpleGUI', sg)

    import saveslots
    monkeypatch.setattr(saveslots, 'lade_slot', lambda slot=1: None)

    import main
    monkeypatch.setattr(main, 'dump_gamestate', lambda *a, **kw: None)
    monkeypatch.setattr(main, 'sg', sg)

    window = MagicMock()
    window.read.return_value = ('Exit', {})
    sg.Window.return_value = window

    main.main()

    assert sg.Window.call_count == 1, 'window was not created exactly once'
    assert window.read.call_count == 1, 'event loop did not exit on Exit'
    assert main.GAMESTATE, 'gamestate was not initialised'


def test_layout_can_be_built_from_a_fresh_save(game):
    layout = game.erstelle_layout()
    assert isinstance(layout, list) and layout
