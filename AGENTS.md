# AGENTS.md — Smart Solutions course repo

This repo belongs to a 3-student team working through the "Smart Solutions"
(Nutikad Lahendused) programming labs. One repo covers the whole course;
each lab gets its own folder under `smart-solutions/labN/`.

## What this course is building toward

Same team, same MG400 robot, same AtomS3 (ESP32) as the other two courses
running in parallel (Data Acquisition & 3D Printing/CAD) — one shared demo
across all three: **press a key on the AtomS3, the robot draws that
letter.** This course's contribution is the "station" (the laptop running
Python): it drives the MG400 over its TCP/IP API (ports 29999/30003/30004),
serves a Flask web UI for jogging/teaching positions and pump control, and
receives the letter chosen on the AtomS3 to turn it into a drawn path. The
Atom firmware itself (image display, captive portal, settings/test page)
also lives here.

- Data Acquisition course repo builds the pressure-sensing/pump-control
  logic and the Atom button → letter selection. See `data-acquisition-course`.
- 3D Printing/CAD course repo builds the pen holder that mounts on the
  robot's flange. See `3d-printing-course`.

## Repo layout

```
smart-solutions/
  lab1/
    README.md    <- official Estonian assignment, copied verbatim, filled in as work happens (KAARDISTA ISE sections)
    src/         <- station code: MG400 base-package client, letter channel (atom_bridge.py), letter->path logic,
                    text layout, paper/robot calibration, station.py (web UI in static/)
    firmware/    <- AtomS3 PlatformIO project (ESP32-Image-Server based: WiFi AP, captive portal, settings/test page,
                    letter button, pump/pressure code in src/pump/)
    config/      <- letters.json, Hershey fonts (fonts/), robot_calibration.json (pen R and Z up/down, speed, paper corners)
    data/        <- positions.json (taught robot positions), letter_events.csv (letters received/drawn)
    docs/        <- atom_page.md, letters.md, letter_channel.md, bom.md, pick_test.csv, latency.csv,
                    mg400_setup.md, robot_calibration.md, robot_runbook.md, text_drawing.md,
                    draw.io diagrams (system.drawio, system_03.10.26.drawio/.svg), images/ (photos)
    tests/       <- pytest: letter paths, motion plan, calibration, mapping, MG400 client, station dry-run/execute
    tools/       <- build_fonts.py (fonts -> config/fonts), latency_report.py (docs/latency.csv)
study-ru/
  lab1-translation.md     <- personal Russian translation, NOT part of the graded submission
  lab1-kaardista-fakty.md <- Russian facts sheet used to fill KAARDISTA ISE sections, NOT graded
```

Each later lab under `smart-solutions/labN/` follows the same pattern.

## Conventions

- **Language:** assignments are issued in Estonian. `README.md` in each lab
  folder stays in Estonian (official template, `KAARDISTA ISE` = "map it
  yourself" fill-in-the-blank sections) — filled in as the student measures
  things. Personal Russian translations live only under `study-ru/`, never
  touching the graded files.
- **Nothing gets deleted.** A wrong measurement stays in the doc with its
  date; the correction goes underneath it, not over it.
- **No fake measurements or hardware claims.** Unknown physical results stay
  `TODO` until a student records the real method, date, value, and units.
- **Devlog entries** live inside each lab's `README.md` under
  "Arenduspäevik" — one entry per work session, appended (not edited later).
- Diagrams/simulations go into the doc as an image + a link to the live,
  editable file (draw.io link).
- Firmware projects use PlatformIO with a reproducible `platformio.ini`, source
  tree, and dependencies; Arduino IDE is not the primary project workflow.
- In Lab 2, Atom initiates outbound HTTPS polling to the public post-office.
  The droplet never connects inbound to the station or MG400, and both camera
  streams stay on the station/local network.
- In Lab 3, do not invent IP addresses, routes, VPN configuration, or network
  measurements. Never store private SSH or WireGuard keys in the repo. The
  public post-office and VPN are separate paths; physical results require real
  hardware, and Lab 3 devlog entries are appended rather than rewritten.
- Lab 3 direct VPN control requires a person in the room at the physical
  e-stop and a working full-table camera; the tool camera alone is insufficient.
  Design, implement, and test connection-loss fail-safe behavior before the
  first remote motion. A software Stop is not a physical e-stop substitute.
- UV activation is local only, never through remote VPN control. Use 405 nm
  eye protection and an opaque enclosure that contains the light; Atom's timer
  must turn the LED off independently of the browser or network connection.
- Coordinate Lab 3 with the current Data Acquisition and 3D Printing documents:
  the Y branch feeds the suction cup directly; the valve controls only the
  syringe, disconnecting the pump and venting the syringe when unpowered.
  Confirm commands and all four tool offsets before implementation; plans,
  examples, CAD, and simulations do not prove physical completion.
- Git tag per lab only at final submission, e.g. `smart-solutions-lab1`.

## Lab 4 · ühine kirje ja töövoog

- Loe [Lab 4 README-d](smart-solutions/lab4/README.md), [kirje ettepanekut](smart-solutions/lab4/docs/record.md) ja [integratsiooni lähtedokumente](smart-solutions/lab4/docs/integration.md). Andmehõive 27 välja ja võti `(team, station_id, cycle)` on **PROPOSED**, kuni kõik osapooled kinnitavad. Säilita jaamas püsiv numeratsioon, katkestatud tsükli jälg, algfailid ja muutumatu kordussaatmise sisu.
- Hoia avalik HTTPS-postkontor eraldi privaatsest WireGuardist, MQTT-st, katsebaasist ja kaameratest. Jaam eemaldab ootel kirje pärast andmebaasi rakenduskinnitust. Puuduv mõõtmine jääb tühjaks. Säilita algne katsekirje ka konflikti või paranduse korral.
- Luba MCP kaudu ainult `guide`, `status`, `look` ja `api` lugemine. Seadmekäsud ja kirjutusrajad on keelatud. Ligipääs on vaikimisi kinni ja ajutine salajane link jääb VPN-i.
- Rakenda operaatorilukk jaamas kõigil käsuradadel ja ühes MG400 lüüsis. CAD Hubi Motion Lock katab Hubi enda liikumisteed. Lab 2 software-only mudel on prototüüp. Lease'i kadu nõuab ohutut kohalikku taastamist enne uut liikumist.
- Kasuta CAD-i vahetuslogi ja kinnitatud konfiguratsiooniviiteid. V3 klaasihoidik on esialgne kandidaat. Seo vahetus tsükli võtme ja ajaga, säilita kontrolli- ning katkestusjälg.
- Kõik Lab 3 ohutusreeglid kehtivad edasi. Kohalik UV-luba, füüsiline hädastopp ja kontrollitud katkestuskäitumine jäävad nõutuks. Plaan, simulatsioon ja tarkvaratest ei tõenda füüsilist katset.

## Tools in play

- Laptop with Ethernet port/adapter; Python 3.11+, venv, pip, Flask.
- MG400 base package: https://github.com/KKallas/mg400-base
- AtomS3 (ESP32), USB-C cable; VS Code + PlatformIO extension; M5Unified.
- ESP32-Image-Server as the firmware starting point:
  https://github.com/KKallas/ESP32-Image-Server
- Phone (to join the Atom's WiFi network and test the captive portal).
- draw.io (system diagrams).

## Safety notes (for anyone, human or agent, drafting instructions)

- MG400 reach is 440 mm; nobody's hands in that area while a command is
  pending. Someone says "moving" before every run.
- The only trusted stop is the physical e-stop on the robot base; the
  on-page stop button is a convenience only.
- First run of any new sequence goes at 20% speed, pen/suction cup 20 mm
  above the surface, no test piece.
- Only one program sends motion commands to the robot at a time.
- Pump box is 24V; DO lines get connected only with the robot disabled and
  the box unpowered.
- Change the Atom's WiFi password away from the default before it leaves
  the lab.

## For an AI agent picking up work here

- Check the current lab's `README.md` first — live goals, checklist, and
  devlog are there; don't duplicate what's already answered.
- This is coursework: the student does the actual measurements/design work
  themselves. Help with translation, explaining concepts, repo/tool setup —
  don't produce the graded numbers, address plans, or devlog entries for
  them.
- If asked to translate assignment text, translate faithfully; don't
  editorialize instructor requirements.
