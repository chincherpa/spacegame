# Spacegame Development Roadmap

This document contains the feature roadmap and TODO items for the Spacegame project.

---

## Feature Status Analysis

### 1. Build System (Bau-System)
**Status**: Working

- `baue()`, `beende_bauen()`, `stoppe_bauen()` work on the running order
  (`sLaufender_Bau`), independent of what is selected in the UI
- Build queue ("In Queue stellen") with a quantity per order; materials are
  taken when an order starts, and an order waits while materials are missing
- Cancelling returns materials for unfinished pieces
- Running build and queue are saved and restored

---

### 2. Planet Travel (Reisen zwischen Planeten)
**Status**: Working

**Current State**:
- `Reise` class with full start/tick/arrival cycle
- Progress indicators in the Reisen tab and HQ overview
- Live travel info (distance, capacity, availability) when selecting options
- Active travels are saved and restored
- Planets are discovered via probe (Raumsonde) launched from HQ

**Implemented**:
- Fuel consumption scales with distance and ship type (`travel_rules.py`)
- Life support consumes water per astronaut per distance unit; a
  `Lebenserhaltung_Upgrade` reduces the demand
- Random events during travel: breakdowns, delays, solar wind, resource finds,
  cargo loss - weighted by distance and resolved deterministically for tests

**TODO**:
- Warn the player when astronauts would be stranded without return fuel

---

### 3. Research System (Forschungssystem)
**Status**: Working

**Current State**:
- Basic mechanics are present
- Research tree with dependencies exists
- Research queue implemented: "In Queue stellen" button appears when research is active; auto-starts next research on completion

**TODO**:
- Add visual connection/list of possible next researches in UI

**Fixed**: research point costs for Rakete (2000) and Weltraumstation (5000)
were far outside the rest of the curve (1-20) and made the endgame
unreachable; they are now 35 and 80. The unused duplicate key
`Kosten Forschungspunkte` was removed.

---

### 4. Inventory/Resource Management & Workshop
**Status**: Working

**Current State**:
- Dynamic display implemented
- Basic material descriptions available
- Log entries capped at 100 (LOG_MAX_ENTRIES enforced)

**Implemented**:
- Inventory rows are created for every material that can ever appear
  (mining, mission, job and travel-event rewards), so finds show up at once
- Inventory value uses `config.MATERIAL_VALUES` (a hardcoded debug value of
  9999999 for Eisenbarren was removed) and includes spaceships

**TODO**:
- Develop resource mining and processing simulator

---

### 5. Moon Missions and Mining
**Status**: Working

- Missions run in the background, in parallel; completed missions are stored
  in the savegame (`GAMESTATE['Mondmissionen']`)
- Missions can depend on other missions (`voraussetzung` in `actions.py`)
- Missions and mining expeditions bind astronauts on the planet; bound
  astronauts cannot start another mission, expedition or journey
- Materials come from the planet's storage (`GAMESTATE['Lager']`), which is
  filled by cargo flights
- Mission rewards have lasting effects: Astronaut_Erfahrung (mining yield),
  Mondstation_Modul (shorter Moon expeditions), Lebenserhaltung_Upgrade (less
  water on journeys), Kommunikations_Upgrade (extra research points)
- Mars mining is the only source of Gold, which the Weltraumstation needs

**Ideas**:
- New mission types (time requirements, rescue missions), Mars missions

---

### 6. UI/UX Improvements
**Status**: Needs work

**Current State**:
- Travel panel shows fuel/life-support consumption and what is missing
- Shop shows sell prices and the proceeds before confirming

**TODO**:
- Develop context-sensitive tooltips and help panels
- Add continuous progress bars and visible status indicators
- Implement feedback for impossible actions
- Create interactive log/message output with filter options

---

### 7. Save/Load System
**Status**: Working

**Current State**:
- Autosave every 150 ticks (~5 min) and after research, build, and mission
  completion, always into the active slot (the one last loaded or saved)
- Running research, build orders, queues and Earth jobs are saved
- Saves are written atomically; an unreadable save is moved to
  `<file>.beschaedigt` instead of being overwritten
- "Neues Spiel" in the File menu restarts in the active slot
- Recipes and distances are game rules: they are always taken from the
  current code, not from the save

**Implemented**:
- Three save slots (`saveslots.py`); slot 1 keeps using `savefile.json`
- File menu offers save/load per slot plus a slot overview showing cycle,
  credits and progress
- Corrupted save files are reported instead of crashing

**TODO**:
- Allow deleting a slot from the UI

---

### 8. Tutorial and Help System
**Status**: Working

**Current State**:
- "Nächstes Ziel" panel in HQ derives the current objective from the save
  state, so it is correct even after loading an old game (`tutorial.py`)
- Short manual shown on first start and available from the Hilfe menu
- Context help per tab

**TODO**:
- Inline tooltips on individual buttons and materials

---

## Feature Concepts

### Moon Missions
- Mission system with various goals (e.g., collect samples, build modules, conduct research)
- Progress display and rewards (e.g., research points, rare materials)
- Risk and event system (e.g., astronauts can gain or lose experience)

### Planet Travel
- Selection of spacecraft, start and destination planet, astronauts and cargo
- Travel time and progress display
- Events during travel (e.g., breakdowns, discoveries)
- Resource consumption (fuel, life support)

### Research System
- Research tree with dependencies
- Research points as resource
- Unlock new technologies and blueprints

### Build System
- Construction of spacecraft, stations and modules
- Material consumption and build time
- Progress display and cancel option

### Inventory and Resource Management
- Dynamic inventory display
- Collect, store and process resources
- Trading system (shop, trade with NPCs)

### Astronaut Management
- Assignment to missions and travels
- Experience, health and skills
- Training and upgrades

### Planet and Station Management
- Expansion of bases and stations
- Management of modules and upgrades
- Discovery of new planets and resources

### Events and Random Encounters
- Random events (meteorites, technical defects, discoveries)
- Decisions with consequences

---

## Completed Core Loop

The game is playable start to finish:
1. Earth jobs generate research points and raw materials
2. Research unlocks workshop recipes (Eisenbarren → ... → Raumsonde → Mondlander → Rakete → Weltraumstation)
3. A built Raumsonde can be launched from HQ; it discovers the Moon, then Mars
4. Discovery unlocks the Planeten, Reisen, Mondmissionen and Mining tabs (no restart needed)
5. Travels move ships, astronauts and cargo between planets; cargo supplies missions and mining on site
6. Moon missions and mining expeditions provide credits, research points and rare materials
7. The Shop sells materials and (researched) spaceships for credits
8. Mars mining yields the Gold for the Weltraumstation
9. Building the Weltraumstation wins the game

### 9. Achievements and Statistics
**Status**: Working

- Lifetime counters (jobs, research, builds, travels, missions, mining,
  credits, sales, travel events) in `GAMESTATE['Statistik']`
- 14 achievements with credit/research rewards, viewable from HQ and the
  Hilfe menu (`achievements.py`)

---

## Testing

`main.py` can be imported without a display: the tests replace FreeSimpleGUI
with `tests/fake_sg.py` (fixture `spiel` in `tests/conftest.py`). The game loop
is split into `verarbeite_tick()` and `verarbeite_event()`, so tests drive the
real logic. `tests/test_durchspielen.py` plays the whole game with a bot and
asserts it can be won.

## Known gaps

- `main.py` is still one large module that mixes layout, state and logic.
- Indentation and naming are not uniform across `main.py`.
- The GUI itself is only covered through the stand-in; layout and visibility
  behaviour of the real toolkit need a manual check.

## Summary

The game is complete and winnable end to end (the bot needs about 1000 cycles,
roughly half an hour). Cargo, storage on Moon and Mars, mission rewards and
Mars gold all feed into the Weltraumstation. Further work would be additional
depth: astronaut management, Mars missions, more planets, base events.
