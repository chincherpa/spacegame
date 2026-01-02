GAMESTATE = {
  'Ticks': 0,
  'Credits': 10,
  'Forschungspunkte': 0,

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
    'Eisenbarren': {
      'erforscht': False,
    },

    'Baumaterial': {
      'erforscht': False,
    },

    'Werkzeug': {
      'erforscht': False,
    },

    'Treibstoff': {
      'erforscht': False,
    },

    'Raumsonde': {
      'erforscht': False,
    },

    'Mondlander': {
      'erforscht': False,
    },

    'Rakete': {
      'erforscht': False,
    },

    'Mondbasen Bauplan': {
      'erforscht': False,
    },

    'Weltraumstation': {
      'erforscht': False,
    },
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
        'Eisenbarren': 5,
        'Werkzeug': 5
      },
    },
    'Mondlander': {
      'beschreibung': 'Text Beschreibung Mondlander',
      'dauer': 2,
      'material': {
        'Eisenbarren': 10,
        'Werkzeug': 10
      },
    },
    'Rakete': {
      'beschreibung': 'Text Beschreibung Rakete',
      'dauer': 2,
      'material': {
        'Eisenbarren': 30,
        'Werkzeug': 20
      },
    },
    'Weltraumstation': {
      'beschreibung': 'Text Beschreibung Weltraumstation',
      'dauer': 10,
      'material': {
        'Mondlander': 5,
        'Eisenbarren': 100,
        'Werkzeug': 10
      },
    },
  },

  'Inventar': {
    # Basis-Materialien
    'Baumaterial': 0,
    'Eisenbarren': 0,
    'Roheisen': 10,      # Für Eisenbarren-Produktion
    'Staub': 5,          # Für Baumaterial
    'Gold': 0,
    'Eisen': 0,
    'Stein': 0,
    'Werkzeug': 0,
    'Wasser': 10,        # Für Produktion
    'Raumsonde': 0,
    # Mondmission-Belohnungen
    'Mondgestein': 0,
    'Seltene_Mineralien': 0,
    'Mondstation_Modul': 0,
    'Astronaut_Erfahrung': 0,
    'Lebenserhaltung_Upgrade': 0,
    'Kommunikations_Upgrade': 0,
    'Mondbasen Bauplan': 0,
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

  'Mondmissionen': {
      'Erkundung und Probenentnahme': {
          'erforscht': False,
      },
      'Konstruktion und Reparatur von Strukturen': {
          'erforscht': False,
          'benötigt_baumaterial': 3,
      },
      'Navigation und Anpassung an die geringere Schwerkraft': {
          'erforscht': False,
      },
      'Raumfahrttechnik und -navigation': {
          'erforscht': False,
      },
      'Geologische Untersuchungen': {
          'erforscht': False,
      },
      'Lebenserhaltungssysteme': {
          'erforscht': False,
      },
      'Kommunikation und Datenübertragung': {
          'erforscht': False,
      },
      'Mondbasen-Design': {
          'erforscht': False,
      }
  },
}
