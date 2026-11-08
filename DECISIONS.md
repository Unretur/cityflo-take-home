# Decision record: 07:45 verdicts, Wednesday 17 June 2026

## Note on the process
The original Cursor chat was deleted when the agent was reset, so the decisions below were made again from the table and are not quoted from the original session. Remaining Cursor usage was used for the stall rule only.

## Verdicts and worry-order
1. Route 11 (TRIP_014, V-06): NO_VERDICT, stalled. Last stop reached was Borivali Stn at 06:46. No stop since. Call the driver.
2. Route 12 (TRIP_015, V-10): PUSH_LATE 9 min at Vikhroli (seq 4), reached 07:39, scheduled 07:30. Push the notice.
3. Route 14 (TRIP_016, V-04): NO_VERDICT, last ping 48 min old. Call the driver.
4. Route 17 (TRIP_017, V-05): NO_VERDICT, last ping 17 min old. Re-check at 08:00.
5. Route 9 (TRIP_013, V-11): HOLD. At JVLR (seq 6), 07:34 against 07:35 scheduled.
6. Route 21 (TRIP_018, V-03): HOLD. At Kurla (seq 4), 07:41 against 07:44 scheduled.
7. Route 21 (TRIP_019, V-09, operator 7): HOLD, flagged. At Amar Mahal (seq 2), 07:40 against 07:40 scheduled.

Why this order: a stalled bus strands riders now. Route 12 is the only confident late verdict. Silent buses may be GPS gaps, so they need a call before a push.

## Decision 1: Baseline is the timetable, with stops evenly spaced in time
- Rule: scheduled time at stop k = start + (end - start) * (k - 1) / (n - 1).
- Breaks on: route 12, TRIP_015. The 9-minute verdict depends on this spacing being right at Vikhroli.
- Cost: a false push burns rider trust. A missed push strands people at a stop.
- Flips if: the timetable publishes stop times, or promised_eta for route 12 boarding stops disagrees with this baseline.

## Decision 2: Clock is received_at, not recorded_at
- Rule: all cutoffs and ages use the server ingest time.
- Breaks on: any ping where received_at lags recorded_at by minutes.
- Cost: a few seconds of error, which doesn't change any verdict above.
- Flips if: a vehicle's received_at lags recorded_at by minutes.

## Decision 3: Stall rule
- Rule: NO_VERDICT if the last stop reached was more than 15 minutes before 07:45 and the bus is not at the final stop.
- Breaks on: TRIP_014. It is the case the rule was written for, and it could also fire on a bus on a long stretch with no stops.
- Cost: Priya makes a call herself, with no verdict to rely on.
- Flips if: pings show TRIP_014 moving between stops without reaching one.

## Decision 4: Route 12 at measured lateness, not 0
- Rule: the contractual on-time commitment is not applied to the verdict. It goes in a separate column.
- Breaks on: TRIP_015. The measured 9 minutes is what riders would be told.
- Cost: a push to route 12 riders. Not pushing hides a real delay from them.
- Flips if: Priya confirms the contract, and the 9 minutes is shown to be a baseline error from decision 1.

## Decision 5: Operator 7 kept in the table with a flag
- Rule: operator 7 vehicles are shown and flagged, and excluded from the worry-order.
- Breaks on: TRIP_019, V-09. It shows HOLD, and dropping it would hide that the bus exists.
- Cost: none on the wall, if Priya reads the flag.
- Flips if: the onboarding SOP is confirmed to require exclusion from the output.
