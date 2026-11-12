MINING_EXPEDITIONEN = {
    'Mond': {
        'beschreibung': 'Astronauten bauen Rohstoffe auf dem Mond ab.',
        'dauer': 4,
        'planet': 'Mond',
        'benötigt_astronauten': 2,
        'benötigt_werkzeug': 1,
        'belohnung': {'Mondgestein': 4, 'Seltene_Mineralien': 1, 'Staub': 3},
        # Astronaut_Erfahrung: +1 Mondgestein je Punkt
        'hauptertrag': 'Mondgestein',
        'erfahrung_pro_bonus': 1,
    },
    'Mars': {
        'beschreibung': 'Astronauten bauen Rohstoffe auf dem Mars ab.',
        'dauer': 6,
        'planet': 'Mars',
        'benötigt_astronauten': 2,
        'benötigt_werkzeug': 1,
        'benötigt_baumaterial': 1,
        # 'Eisenerz' war ein Duplikat von 'Roheisen' ohne Inventarplatz.
        'belohnung': {'Roheisen': 8, 'Gold': 1, 'Seltene_Mineralien': 1},
        # Astronaut_Erfahrung: +1 Gold je 3 Punkte. Gold ist der Grund für die
        # Marsreise, aber knapp gehalten (die Weltraumstation braucht 3).
        'hauptertrag': 'Gold',
        'erfahrung_pro_bonus': 3,
    },
}
