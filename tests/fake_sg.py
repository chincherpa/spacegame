"""
Minimaler Ersatz für FreeSimpleGUI, damit main.py ohne Fenster importiert und
getestet werden kann.

Der Ersatz ist bewusst streng: `window[key]` wirft KeyError für Keys, die im
Layout nicht vorkommen. So fallen Tippfehler in Element-Keys in den Tests auf.
"""
import types


class FakeElement:
    def __init__(self, typ, args, kwargs):
        self.typ = typ
        self.args = args
        self.key = kwargs.get('key')
        self.visible = kwargs.get('visible', True)
        self.value = kwargs.get('initial_value', kwargs.get('default_value'))
        if self.value is None and typ in ('Text', 'Multiline') and args:
            self.value = args[0]
        self.kwargs = dict(kwargs)

    def update(self, *args, **kwargs):
        if args:
            self.value = args[0]
        if 'value' in kwargs:
            self.value = kwargs['value']
        if 'visible' in kwargs:
            self.visible = kwargs['visible']
        self.kwargs.update(kwargs)

    def get(self):
        return self.value

    def select(self):
        pass


def _sammle(obj, gefunden):
    """Sammelt rekursiv alle Elemente mit Key aus einem verschachtelten Layout."""
    if isinstance(obj, FakeElement):
        if obj.key is not None:
            if obj.key in gefunden:
                raise ValueError(f'Doppelter Element-Key im Layout: {obj.key!r}')
            gefunden[obj.key] = obj
        for arg in obj.args:
            _sammle(arg, gefunden)
    elif isinstance(obj, (list, tuple)):
        for teil in obj:
            _sammle(teil, gefunden)


class FakeWindow:
    def __init__(self, titel, layout, **kwargs):
        self.elemente = {}
        _sammle(layout, self.elemente)
        self.geschlossen = False

    def __getitem__(self, key):
        return self.elemente[key]

    def read(self, timeout=None):
        return TIMEOUT_KEY, {}

    def bind(self, *args):
        pass

    def refresh(self):
        pass

    def close(self):
        self.geschlossen = True


TIMEOUT_KEY = '__TIMEOUT__'
WINDOW_CLOSED = None


def erstelle_modul():
    """Liefert ein frisches Modulobjekt, das sich wie FreeSimpleGUI anfühlt."""
    modul = types.ModuleType('FreeSimpleGUI')
    modul.TIMEOUT_KEY = TIMEOUT_KEY
    modul.WINDOW_CLOSED = WINDOW_CLOSED
    modul.Window = FakeWindow
    modul.popups = []            # Protokoll aller Popups: (name, args)
    modul.antwort_ja_nein = 'Yes'

    def popup(name, rueckgabe=None):
        def zeige(*args, **kwargs):
            modul.popups.append((name, args))
            return modul.antwort_ja_nein if name == 'popup_yes_no' else rueckgabe
        return zeige

    for name in ('popup', 'popup_no_wait', 'popup_scrolled', 'popup_yes_no'):
        setattr(modul, name, popup(name))
    modul.theme = lambda *a, **k: None
    modul.theme_button_color = lambda *a, **k: ('white', 'blue')

    def __getattr__(name):
        # Alles andere (Text, Button, Column, ...) ist ein Element.
        if name.startswith('__'):
            raise AttributeError(name)
        return lambda *args, **kwargs: FakeElement(name, args, kwargs)

    modul.__getattr__ = __getattr__
    return modul
