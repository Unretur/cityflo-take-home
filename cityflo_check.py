import sys, math
from pathlib import Path
import pandas as pd

D = Path(sys.argv[1])
CUTOFF = pd.Timestamp("2026-06-17 07:45:00")   # Priya's standup cutoff, IST
DAY = "06-17"
FRESH_MIN = 5          # ping older than this -> NO_VERDICT
NEAR_STOP_M = 150      # within this of a stop = arrived (brief: don't trust sub-100 m detail)
OFF_ROUTE_M = 300      # farther than this from the stop polyline -> NO_VERDICT
LATE_MIN = 5           # lateness at or above this -> PUSH_LATE

def ts(day, hm):
    day, hm = str(day), str(hm)
    if len(hm) > 8:
        return pd.to_datetime(hm, utc=True).tz_convert("Asia/Kolkata").tz_localize(None)
    full = day if len(day) == 10 else "2026-" + day
    return pd.to_datetime(full + " " + hm)

def hav(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def seg_dist(lat, lon, a, b):
    kx = 111320*math.cos(math.radians(lat)); ky = 110574
    px, py = (lon-a[1])*kx, (lat-a[0])*ky
    bx, by = (b[1]-a[1])*kx, (b[0]-a[0])*ky
    L = bx*bx + by*by
    u = 0 if L == 0 else max(0, min(1, (px*bx + py*by)/L))
    return math.hypot(px-u*bx, py-u*by)

pings = pd.read_csv(D/"data/gps_pings.csv", dtype={"vehicle_id": str})
trips = pd.read_csv(D/"data/trips.csv", dtype=str)
stops = pd.read_csv(D/"data/stops.csv", dtype={"route_id": str})
pings["received_at"] = pd.to_datetime(pings["received_at"], errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
print("pings:", len(pings), "| unparsed received_at:", pings.received_at.isna().sum())

day_trips = trips[trips.service_date.str.endswith(DAY)]
out = []
for _, tr in day_trips.iterrows():
    st = stops[stops.route_id == tr.route_id].sort_values("seq").reset_index(drop=True)
    n = len(st)
    s0 = ts(tr.service_date, tr.scheduled_start)
    s1 = ts(tr.service_date, tr.scheduled_end)
    sched = [s0 + (s1 - s0)*k/(n-1) for k in range(n)]   # ASSUMPTION: stops evenly spaced in time
    flag = ""
    if tr.route_id == "12": flag = "rev C on-time override NOT applied"
    vp = pings[(pings.vehicle_id == tr.vehicle_id) &
               (pings.received_at <= CUTOFF) &
               (pings.received_at >= s0 - pd.Timedelta(minutes=30))].sort_values("received_at")
    if vp.empty:
        out.append(dict(trip=tr.trip_id, route=tr.route_id, vehicle=tr.vehicle_id, operator="",
                        verdict="NO_VERDICT", detail="no pings before cutoff", flag=flag)); continue
    last = vp.iloc[-1]
    op = int(last.operator_id)
    if op == 7: flag = (flag + "; " if flag else "") + "operator 7, excluded from lateness per rev C, shown"
    age = (CUTOFF - last.received_at).total_seconds()/60
    pts = list(zip(st.lat, st.lon))
    dmin = min(seg_dist(last.lat, last.lon, pts[i], pts[i+1]) for i in range(n-1))
    arrivals = {}
    for k in range(n):
        d = vp.apply(lambda r: hav(r.lat, r.lon, st.loc[k, "lat"], st.loc[k, "lon"]), axis=1)
        hit = vp[d < NEAR_STOP_M]
        if not hit.empty: arrivals[k] = hit.received_at.iloc[0]
    recent = vp[vp.received_at >= CUTOFF - pd.Timedelta(minutes=5)]
    if age > FRESH_MIN:
        v, det = "NO_VERDICT", f"last ping {age:.0f} min old"
    elif dmin > OFF_ROUTE_M:
        v, det = "NO_VERDICT", f"{dmin:.0f} m from route line"
    elif len(recent) and (recent.speed_kmph < 2).all() and dmin > NEAR_STOP_M:
        v, det = "CALL_DRIVER", "stationary 5+ min away from stops"
    elif arrivals and (CUTOFF - arrivals[max(arrivals)]).total_seconds()/60 > 15 and max(arrivals) < n-1:
        v, det = "NO_VERDICT", "stalled or GPS gap"
    elif not arrivals: 
        v, det = "NO_VERDICT", "no stop reached yet"
    else:
        k = max(arrivals)
        late = (arrivals[k] - sched[k]).total_seconds()/60
        v = f"PUSH_LATE {late:.0f} min" if late >= LATE_MIN else "HOLD"
        det = f"at {st.loc[k,'stop_name']} (seq {st.loc[k,'seq']}) {arrivals[k]:%H:%M}, sched {sched[k]:%H:%M}"
    out.append(dict(trip=tr.trip_id, route=tr.route_id, vehicle=tr.vehicle_id, operator=op,
                    verdict=v, detail=det, flag=flag))

res = pd.DataFrame(out)
res.to_csv(D/"verdicts_17jun.csv", index=False)
print(res.to_string(index=False))