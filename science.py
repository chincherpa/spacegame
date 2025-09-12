SCIENCE = {
  'Eisenbarren': {
    'beschreibung': 'Erforsche die Produktion von Eisenbarren. Aus Eisenbarren kannst du Baumaterial und Werkzeug herstellen',
    'erforschbar nach': '',
    'dauer': 3,
    'kosten': 5,
  },

  'Baumaterial': {
    'beschreibung': 'Erforsche das Herstellen von Baumaterial aus den auf dem Mond verfügbaren Ressourcen. Mit Baumaterial kannst du Weltraumstationen bauen.',
    'erforschbar nach': 'Baumaterial',
    'dauer': 3,
    'kosten': 1,
  },

  'Werkzeug': {
    'beschreibung': 'Erforsche die Herstellung von Werkzeug aus Eisenbarren. Mit Werkzeug und Baumaterial kannst du eine Weltraumstation bauen.',
    'erforschbar nach': 'Werkzeug',
    'dauer': 5,
    'kosten': 2,
  },

  'Treibstoff': {
    'beschreibung': 'Erforschung der Herstellung von Treibstoff aus den auf dem Mond verfügbaren Ressourcen',
    'erforschbar nach': 'Treibstoff',
    'dauer': 6,
    'kosten': 4,
    },

  'Raumsonde': {
    'beschreibung': 'Erforsche den Bau einer Raumsonde. Mit einer Raumsonde kannst du den Weltraum erforschen und andere Planeten entdecken. Flüge mit einer Raumsonde geben Forschungspunkte.',
    'erforschbar nach': 'Treibstoff',
    'Sitzplätze': 0,
    'Frachtplätze': 0,
    'Kosten Forschungspunkte': 5,
    'dauer': 8,
    'reichweite': 10,
    'kosten': 10,
  },

  'Mondlander': {
    'beschreibung': 'Mit dem Mondlander kannst du zum Mond fliegen.',
    'erforschbar nach': 'Raumsonde',
    'Sitzplätze': 2,
    'Frachtplätze': 3,
    'Kosten Forschungspunkte': 10,
    'dauer': 10,
    'reichweite': 1,
    'kosten': 10,
  },

  'Rakete': {
    'beschreibung': 'Erforsche den Bau einer Rakete. Mit einer Rakete kannst du zu Planeten fliegen.',
    'erforschbar nach': 'Mondlander',
    'Sitzplätze': 5,
    'Frachtplätze': 6,
    'Kosten Forschungspunkte': 20,
    'dauer': 20,
    'reichweite': 10,
    'kosten': 2000,
  },

  'Mondbasen Bauplan': {
    'beschreibung': 'Baupläne für Mondbasen',
    'erforschbar nach': 'Rakete',
    'Kosten Forschungspunkte': 5,
    'dauer': 5,
    'kosten': 5,
  },

  'Weltraumstation': {
    'beschreibung': 'Erforsche den Bau einer Weltraumstation.',
    'erforschbar nach': 'Mondbasen Bauplan',
    'dauer': 50,
    'kosten': 5000,
  },
}
