MINING_EXPEDITIONEN = {
    'Mond': {
        'beschreibung': 'Astronauten bauen Rohstoffe auf dem Mond ab.',
        'dauer': 4,
        'planet': 'Mond',
        'benötigt_astronauten': 2,
        'benötigt_werkzeug': 1,
        'belohnung': {'Mondgestein': 4, 'Seltene_Mineralien': 1, 'Staub': 3},
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
    },
}
