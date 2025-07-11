GAMESTATE = {
  'Ticks': 0,
  'Credits': 50,
  'Forschungspunkte': 20,

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
      'dauer': 0.1,
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

  'Werkstatt': {
    'Baumaterial': {
      'beschreibung': 'Text Beschreibung Baumaterial',
      'dauer': 2,
      'material': {
        'Staub': 1,
        'Wasser': 1
      },
    },
    'Eisenbarren': {
      'beschreibung': 'Text Beschreibung Eisenbarren',
      'dauer': 2,
      'material': {
        'Roheisen': 1
      },
    },
    'Werkzeug': {
      'beschreibung': 'Text Beschreibung Eisenbarren',
      'dauer': 2,
      'material': {
        'Eisenbarren': 1,
        'Wasser': 1
      },
    },
    'Raumsonde': {
      'beschreibung': 'Text Beschreibung Raumsonde',
      'dauer': 2,
      'material': {
        'Eisenbarren': 1,
        'Werkzeug': 1
      },
    },
    'Mondlander': {
      'beschreibung': 'Text Beschreibung Mondlander',
      'dauer': 2,
      'material': {
        'Eisenbarren': 2,
        'Werkzeug': 1
      },
    },
    'Rakete': {
      'beschreibung': 'Text Beschreibung Rakete',
      'dauer': 2,
      'material': {
        'Eisenbarren': 3,
        'Werkzeug': 1
      },
    },
    'Weltraumstation': {
      'beschreibung': 'Text Beschreibung Weltraumstation',
      'dauer': 10,
      'material': {
        'Mondlander': 5,
        'Eisenbarren': 30,
        'Werkzeug': 10
      },
    },
  },

  'Inventar': {
    'Baumaterial': 0,
    'Eisenbarren': 0,  # Hinzugefügt
    'Roheisen': 10,    # Hinzugefügt für Eisenbarren-Produktion
    'Staub': 5,        # Hinzugefügt für Baumaterial
    'Gold': 0,
    'Eisen': 0,
    'Stein': 0,
    'Werkzeug': 0,
    'Wasser': 10,      # Erhöht für Produktion
    'Raumsonde': 0,    # Hinzugefügt
  },

  'Planeten': {
    'Erde': {
      'Entfernung': {
        'Mond': 1,
        'Mars': 3,
      }
    },
    'Mond': {
      'entdeckt': False,
      'Entfernung': {
        'Erde': 1,
        'Mars': 2,
      }
    },
    'Mars': {
      'entdeckt': False,
      'Entfernung': {
        'Erde': 3,
        'Mond': 2,
      }
    },
  },

  'Log': ['Spiel gestartet'],

}