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
**Status**: Partially implemented

**Current State**:
- `Reise` class exists with methods like `starte_reise()`
- Basic travel logic implemented

**TODO**:
- Add progress indicators in UI for ongoing/completed travels
- Implement tick logic for travel and automatic completion handling
- Add random events during travel (breakdowns, discoveries)
- Implement fuel consumption and life support resource usage

---

### 3. Research System (Forschungssystem)
**Status**: Working

**Current State**:
- Basic mechanics are present
- Research tree with dependencies exists

**TODO**:
- Improve prerequisite checking for "erforschbar nach"
- Add visual connection/list of possible next researches in UI
- Implement research queue system

---

### 4. Inventory/Resource Management & Workshop
**Status**: Working

**Current State**:
- Dynamic display implemented
- Basic material descriptions available

**TODO**:
- Ensure new/found materials can always be displayed immediately
- Extend workshop with recipe queries and production chains
- Develop resource mining and processing simulator

---

### 5. Moon Missions (Mondmissionen)
**Status**: Partially implemented

**Current State**:
- Basic structure exists
- Mission start/cancel/completion is mapped

**TODO**:
- Add mission progress in background (parallel to other actions)
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
**Status**: Basic implementation

**Current State**:
- Single savefile support exists

**TODO**:
- Add autosave after important changes
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

## Summary

The game is solidly pre-structured, but essential core features (order queues for building/research/missions; complete travel cycle; event systems; mature UI operation; tutorials) are still unfinished or error-prone. Further development should start at these points, focusing on modularity, error handling, user guidance and the possibility of subsequent expansion (new research, materials, mission types, etc.).
