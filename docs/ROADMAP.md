# Spacegame Development Roadmap

This document contains the feature roadmap and TODO items for the Spacegame project.

---

## Feature Status Analysis

### 1. Build System (Bau-System)
**Status**: Partially implemented

**Current State**:
- Functions for starting/ending build processes exist (`baue()`, `beende_bauen()`)
- Queue system for multiple build orders implemented

**TODO**:
- Improve error handling (e.g., return materials when build is cancelled)
- Add optional build completion notifications in the log
- Synchronize build progress with UI/progress bar and inventory

---

### 2. Planet Travel (Reisen zwischen Planeten)
**Status**: Working

**Current State**:
- `Reise` class with full start/tick/arrival cycle
- Progress indicators in the Reisen tab and HQ overview
- Live travel info (distance, capacity, availability) when selecting options
- Active travels are saved and restored
- Planets are discovered via probe (Raumsonde) launched from HQ

**TODO**:
- Add random events during travel (breakdowns, discoveries)
- Implement fuel consumption and life support resource usage

---

### 3. Research System (Forschungssystem)
**Status**: Working

**Current State**:
- Basic mechanics are present
- Research tree with dependencies exists
- Research queue implemented: "In Queue stellen" button appears when research is active; auto-starts next research on completion

**TODO**:
- Improve prerequisite checking for "erforschbar nach"
- Add visual connection/list of possible next researches in UI

---

### 4. Inventory/Resource Management & Workshop
**Status**: Working

**Current State**:
- Dynamic display implemented
- Basic material descriptions available
- Log entries capped at 100 (LOG_MAX_ENTRIES enforced)

**TODO**:
- Ensure new/found materials can always be displayed immediately
- Extend workshop with recipe queries and production chains
- Develop resource mining and processing simulator

---

### 5. Moon Missions (Mondmissionen)
**Status**: Working

**Current State**:
- Mission start/cancel/completion is mapped
- Missions run in the background, in parallel to other actions
- Completed missions are persisted in the savegame

**TODO**:
- Make rewards/dependencies more flexible (chain missions, random modifiers)
- Create new mission types (time requirements, rescue missions)

---

### 6. UI/UX Improvements
**Status**: Needs work

**TODO**:
- Develop context-sensitive tooltips and help panels
- Add continuous progress bars and visible status indicators
- Implement feedback for impossible actions
- Create interactive log/message output with filter options

---

### 7. Save/Load System
**Status**: Working

**Current State**:
- Single savefile support exists
- Autosave every 150 ticks (~5 min) and after research, build, and mission completion
- Manual save/load via File menu

**TODO**:
- Implement UI feedback for successful save/restore
- Enable multiple savegames and overview load menu

---

### 8. Tutorial and Help System
**Status**: Not started

**TODO**:
- Add start tutorial (modal window, explanatory texts for first steps)
- Implement context-dependent help for unknown buttons/materials

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
5. Travels move ships, astronauts and cargo between planets
6. Moon missions and mining expeditions provide credits, research points and rare materials
7. The Shop sells materials and (researched) spaceships for credits
8. Building the Weltraumstation wins the game

## Summary

The core loop is complete and winnable. Remaining work is depth and polish: random events, fuel consumption, multiple save slots, a tutorial and astronaut management.
