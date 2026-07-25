hier sind alle offenen TODOs geordnet nach Aufwand:

Erledigt:
  - Materialien-Rückgabe bei Bau-Abbruch
  - UI-Feedback nach Speichern ("Spiel gespeichert" Meldung)
  - Voraussetzungen im Forschungs-UI besser anzeigen
  - Reise-Fortschrittsanzeige im UI (Reisen-Tab + HQ-Übersicht)
  - Workshop: Rezept-Abfragen & Produktionsketten (Rohstoffe gesamt)
  - Mondmissionen parallel im Hintergrund
  - Planeten-Reisen: Tick-Logik & automatische Ankunft
  - Raumsonde: Start-Button funktioniert, entdeckt Mond und Mars
  - Shop: Materialien und Raumschiffe gegen Credits kaufen
  - Forschung kostet jetzt Forschungspunkte (Rückerstattung bei Abbruch)
  - Reisen/Raumsonde/Missionen werden gespeichert und wiederhergestellt
  - Siegbedingung: Weltraumstation bauen = Spiel gewonnen
  - Tabs/UI schalten sich bei Entdeckung ohne Neustart frei
  - Weltraumstation ist tatsächlich baubar (Mondlander aus dem Raumschiff-Bestand)
  - Treibstoff hat ein Werkstatt-Rezept
  - Reisen: Treibstoffverbrauch und Lebenserhaltung
  - Reisen: Zufallsereignisse (Pannen, Funde, Sonnenwind)
  - Shop: Materialien verkaufen
  - Wirtschaft neu ausbalanciert (Missions- und Forschungskosten)
  - Mehrere Speicherslots (3 Slots mit Übersicht)
  - Tutorial: "Nächstes Ziel" im HQ + Kurzanleitung + Hilfe pro Tab
  - Erfolge und Statistik
  - Neue Materialien erscheinen sofort im Inventar
  - main.py ist importierbar: kein Fenster und keine Endlosschleife mehr auf
    Modulebene, dafür main() mit __main__-Guard
  - Tests laufen gegen den echten Code in main.py statt gegen Kopien davon
  - core/ und ui/ (toter Code, von main.py nie benutzt) entfernt
  - config.py enthält nur noch Konstanten, die auch gelesen werden
  - Spielstände (savefile*.json) sind nicht mehr im Git

Mittel:
  - Mining/Missionen: mehr Belohnungsvielfalt, verkettete Missionen
  - Mondstation_Modul und Kommunikations_Upgrade mit echter Wirkung versehen
    (Lebenserhaltung_Upgrade senkt bereits den Wasserbedarf auf Reisen)
  - Rückflug-Warnung, wenn Astronauten ohne Treibstoff auf einem Planeten stranden

Groß:
  - Astronauten-Management (Erfahrung, Skills, Namen)
  - Mars-Basis mit eigenen Missionen
  - main.py weiter entflechten: der Einstiegspunkt ist jetzt sauber
    (main() / initialisiere_spielstand() / erstelle_layout() / starte_ui() /
    spiel_schleife()), aber Spiellogik und window[...]-Aufrufe stecken noch in
    denselben Funktionen. Nächster Schritt: reine Logik nach Vorbild von
    travel_rules.py in eigene, GUI-freie Module ziehen.
  - lade_spielstand() und initialisiere_spielstand() machen fast dasselbe;
    zusammenführen, sobald die UI-Aufrufe getrennt sind.

Sehr groß / Konzept:
  - Weitere Planeten und ein größeres Sonnensystem
  - Zufallsereignisse außerhalb von Reisen (Meteore, Pannen in der Basis)
