# ConcreteJungle — Performance Profiling

## Context

ConcreteJungle's hot path is the ambush spawn system (`SpawnAmbushHelper`), which fires on building destruction during combat. It performs raycasts, unit spawning, and AI target assignment. All of this runs inside the BattleTech game process and cannot be isolated without game DLLs.

---

## dotnet-trace Profiling

### Prerequisites

```bash
dotnet tool install -g dotnet-trace
```

### Step 1 — Set up a good test mission

Choose or create a contract with:
- Dense urban terrain (many destructible buildings)
- A faction that triggers ConcreteJungle ambushes
- A large lance to maximise building destruction events

The more building destruction events per minute, the higher the signal density in the trace.

### Step 2 — Find the BattleTech process

```bash
PID=$(pgrep -f "BattleTech.x86_64")
# or: pgrep -f "BattleTech"
```

### Step 3 — Capture a profile during building destruction

Start the trace, then play through one full round of heavy urban combat with building destructions:

```bash
dotnet-trace collect --process-id $PID \
  --duration 00:01:00 \
  --profile cpu-sampling \
  --output concretejungle-combat.nettrace
```

### Step 4 — Analyse

Open in SpeedScope (`speedscope.app`) or PerfView.

**Key methods to find:**

| Class | Method | Why it matters |
|---|---|---|
| `SpawnAmbushHelper` | `SpawnAmbush` | Main ambush entry point; ray cast from above |
| `SpawnAmbushHelper` | `GetSpawnPoint` | Raycast loop — may be called multiple times per ambush |
| `TurretPatches` | `Prefix`/`Postfix` | Harmony intercept on turret spawning methods |
| `TurnDirectorPatches` | `Prefix` | If patching per-turn methods, check for every-frame firing |

---

## What to look for

- **Raycast overhead:** The recent spawn-from-above change introduced a raycast per unit placement. If `SpawnAmbushHelper.GetSpawnPoint` shows significant time, investigate how many raycast attempts occur per failed placement.
- **Harmony patch frequency:** `TurretPatches` and `TurnDirectorPatches` intercept game methods. If those game methods are called every frame or every unit action, the patch cost accumulates.
- **Unit teleport + building teardown sequencing:** The current spawn flow creates units off-screen and teleports them after building destruction. If frame hitches occur at that point, look for sync-point overhead in the sequence.

---

## Frame timing observation (alternative to dotnet-trace)

If dotnet-trace is inconvenient, watch Unity's frame time counter:

1. Enable BattleTech's dev console (Ctrl+Shift+` in some mod setups)
2. Run `fps` or similar to display frame time
3. Trigger an ambush and note the frame time spike at the moment of spawn

Any spike > 100 ms on a modern machine is worth investigating with dotnet-trace.
