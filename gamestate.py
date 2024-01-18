GAMESTATE = {
  'Ticks': 10,
  'Credits': 999,
  'Forschungspunkte': 80,
  'Astronauten': {
    'Erde': 10,
    'Mond': 0,
    'Mars': 0
  },

  'Arbeiter': {
    'Erde': 10,
    'Mond': 0,
    'Mars': 0
  },

  'Raumschiffe': {
    'Erde': {
      'Mondlander': {
        'Anzahl': 0
      },
      'Rakete': {
        'Anzahl': 0
      }
    },
    'Mond': {
      'Mondlander': {
        'Anzahl': 0
      },
      'Rakete': {
        'Anzahl': 0
      }
    },
    'Mars': {
      'Mondlander': {
        'Anzahl': 0
      },
      'Rakete': {
        'Anzahl': 0
      }
    },
  },

  'Forschung': {
    'Baumaterial': {
      'beschreibung': 'Erforsche das Herstellen von Baumaterial aus den auf dem Mond verfügbaren Ressourcen. Mit Baumaterial kannst du Weltraumstationen bauen.',
      'dauer': 3,
      'kosten': 10,
      'erforscht': False,
    },

    'Eisenbarren': {
      'beschreibung': 'Erforsche die Produktion von Eisenbarren. Aus Eisenbarren kannst du Baumaterial und Werkzeug herstellen',
      'dauer': 0.5,
      'kosten': 10,
      'erforscht': False,
    },

    'Mondlander': {
      'beschreibung': '''Mit dem Mondlander kannst du zum Mond fliegen.

Sitzplätze: 2
Frachtplätze: 3
Kosten Forschungspunkte: 10''',
      'dauer': 10,
      'kosten': 10,
      'erforscht': False,
    },

    'Rakete': {
      'beschreibung': '''Erforsche den Bau einer Rakete. Mit einer Rakete kannst du zu Planeten fliegen.

Sitzplätze: 5
Frachtplätze: 6
Kosten Forschungspunkte: 20''',
      'dauer': 20,
      'kosten': 10,
      'erforscht': False,
    },

    'Raumsonde': {
      'beschreibung': '''Erforsche den Bau einer Raumsonde. Mit einer Raumsonde kannst du den Weltraum erforschen und andere Planeten entdecken.
Flüge mit einer Raumsonde geben Forschungspunkte.

Sitzplätze: 0
Frachtplätze: 0
Kosten Forschungspunkte: 5''',
      'dauer': 3,
      'kosten': 10,
      'erforscht': False,
    },

    'Werkzeug': {
      'beschreibung': 'Erforsche die Herstellung von Werkzeug aus Eisenbarren. Mit Werkzeug und Baumaterial kannst du eine Weltraumstation bauen.',
      'dauer': 5,
      'kosten': 10,
      'erforscht': False,
    },

    'Weltraumstation': {
      'beschreibung': 'Erforsche den Bau einer Weltraumstation.',
      'dauer': 5,
      'kosten': 10,
      'erforscht': False,
    },

  # 'Treibstoff': {
  #   'beschreibung': 'Erforschung der Herstellung von Treibstoff aus den auf dem Mond verfügbaren Ressourcen',
  #   'dauer': 6,
  #   'kosten': 10,
  #   'erforscht': False,
  #   },

  },

  'Inventar': {
    "Baumaterial": 18,
    "Staub": 28,
    "Gold": 38,
    "Eisen": 48,
    "Stein": 58,
    "Werkzeug": 68,
    "Wasser": 78,
  },

  'Planeten': {
    'Erde': {
      'Entfernung': {
        'Mond': 1,
        'Mars': 3,
      }
    },
    'Mond': {
      'Entfernung': {
        'Erde': 1,
        'Mars': 2,
      }
    },
    'Mars': {
      'Entfernung': {
        'Erde': 3,
        'Mond': 2,
      }
    },
  },

  'Log': ['Spiel gestartet'],

}