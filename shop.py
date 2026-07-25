SHOP = {
  'Mondlander': {
    'Kosten': 150,
    'Sitze': 2,
    'Frachtplätze': 3,
    'Reichweite': 1,
    'Tank': 1,
  },
  'Rakete': {
    'Kosten': 500,
    'Sitze': 5,
    'Frachtplätze': 10,
    'Reichweite': 5,
    'Tank': 5,
  },
}

# Materialien, die im Shop gegen Credits gekauft werden können
SHOP_MATERIALIEN = {
  'Roheisen': {
    'Kosten': 5,
    'Beschreibung': 'Rohes Eisenerz - Grundlage für Eisenbarren.',
  },
  'Staub': {
    'Kosten': 2,
    'Beschreibung': 'Staub für die Baumaterial-Produktion.',
  },
  'Wasser': {
    'Kosten': 3,
    'Beschreibung': 'Wasser für Lebenserhaltung und Produktion.',
  },
  'Baumaterial': {
    'Kosten': 15,
    'Beschreibung': 'Fertiges Baumaterial für Konstruktionen.',
  },
  'Werkzeug': {
    'Kosten': 25,
    'Beschreibung': 'Werkzeug für komplexe Konstruktionen und Missionen.',
  },
}

# =============================================================================
# VERKAUF
# =============================================================================

# Verkaufspreise pro Stück. Bewusst unterhalb der Einkaufspreise, damit sich
# reines Hin- und Herhandeln nicht lohnt. Materialien, die hier nicht
# aufgeführt sind, können nicht verkauft werden.
VERKAUFSPREISE = {
  'Staub': 1,
  'Wasser': 1,
  'Roheisen': 2,
  'Baumaterial': 4,
  'Eisenbarren': 8,
  'Werkzeug': 12,
  'Treibstoff': 10,
  'Mondgestein': 40,
  'Seltene_Mineralien': 90,
  'Gold': 150,
  'Mondstation_Modul': 120,
  'Raumsonde': 200,
}

# Fortschrittsrelevante Gegenstände sollen nicht versehentlich verkauft werden.
NICHT_VERKAUFBAR = {
  'Mondbasen Bauplan',
  'Lebenserhaltung_Upgrade',
  'Kommunikations_Upgrade',
  'Astronaut_Erfahrung',
}


def ist_verkaufbar(material):
  """Kann dieses Material im Shop verkauft werden?"""
  return material in VERKAUFSPREISE and material not in NICHT_VERKAUFBAR


def verkaufspreis(material, menge=1):
  """Gesamterlös für `menge` Einheiten. 0, wenn nicht verkaufbar."""
  if not ist_verkaufbar(material):
    return 0
  return VERKAUFSPREISE[material] * max(0, int(menge))


def verkaufbare_materialien(inventar):
  """Alle verkaufbaren Materialien mit Bestand > 0, alphabetisch sortiert."""
  return sorted(
    material for material, menge in inventar.items()
    if menge > 0 and ist_verkaufbar(material)
  )


def verkaufe(inventar, material, menge):
  """Verkauft Material aus dem Inventar.

  Verändert `inventar` in place und liefert (erfolg, erlös, meldung).
  """
  menge = int(menge)
  if menge <= 0:
    return False, 0, 'Ungültige Menge'
  if not ist_verkaufbar(material):
    return False, 0, f"'{material}' kann nicht verkauft werden"
  bestand = inventar.get(material, 0)
  if bestand < menge:
    return False, 0, f'Nicht genug {material} im Inventar (vorhanden: {bestand})'
  erloes = verkaufspreis(material, menge)
  inventar[material] = bestand - menge
  return True, erloes, f'{menge}x {material} für {erloes} Credits verkauft'
