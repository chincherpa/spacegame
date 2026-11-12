Stand der Arbeiten:

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
  - UI-Politur: Logbuch sichtbar, Statusleiste sofort aktuell (inkl. freie
    Arbeiter), lesbare Akzentfarben, helle Tab-Icons + eigenes Arbeit-Icon,
    Text-Fortschrittsbalken, Planeten-Infos, Tastenkürzel (Strg+S, F1)

  - Code-Review-Befunde behoben (docs/CODE_REVIEW.md): Auswahl und laufender
    Auftrag getrennt, aktiver Speicherslot, laufende Forschung/Bau gespeichert,
    Astronautenbindung, Bau-Warteschlange, Shop-Daten, atomares Speichern
  - Fracht hat eine Funktion: Lager auf Mond und Mars versorgen Missionen und Mining
  - Verkettete Mondmissionen
  - Missionsbelohnungen wirken (Erfahrung, Mondstation_Modul, Upgrades)
  - Mars liefert das Gold für die Weltraumstation
  - Rückflug-Warnung bei zu wenig Treibstoff
  - "Neues Spiel" im Menü
  - Tests laufen gegen die echte Spiellogik; ein Bot spielt bis zum Sieg durch
  - core/ und ui/ entfernt (ungenutzter, veralteter Zweitentwurf)
  - Planetenlager in beide Richtungen: Erträge von Missionen und Mining liegen im
    Lager vor Ort, Abflüge verbrauchen Treibstoff und Wasser von dort
  - Mehr Frachtplätze (Mondlander 6, Rakete 12) und mehr Frachtgüter
  - Erd-Jobs lassen sich automatisch wiederholen
  - Spiel startet mit dem zuletzt benutzten Slot
  - Bau-Warteschlange zeigt, worauf der vorderste Auftrag wartet
  - Kein Fehler-Popup mehr beim Schliessen über das X
  - Inventarwert rechnet mit Verkaufspreisen
  - Eisenbarren schmelzen in 1 Zyklus, die Weltraumstation braucht 50 statt 100
  - Astronaut_Erfahrung bringt auf dem Mars Gold statt Roheisen

Ideen für später:
  - Astronauten-Management (Erfahrung pro Person, Skills, Namen aus shipnames.py)
  - Mars-Basis mit eigenen Missionen
  - Weitere Planeten und ein größeres Sonnensystem
  - Zufallsereignisse außerhalb von Reisen (Meteore, Pannen in der Basis)
  - Slot aus dem UI löschen
  - main.py in Layout, Zustand und Logik aufteilen; Einrückung vereinheitlichen
