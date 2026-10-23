"""Generate active subway line-station-hours from a dated static GTFS snapshot.

GTFS times use noon minus twelve hours on the service date, per specification.
Frequencies-based service is rejected until expanded explicitly.
"""

import csv
import io
import zipfile
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def seconds(value):
    h, m, s = map(int, value.split(":"))
    if h < 0 or not 0 <= m < 60 or not 0 <= s < 60:
        raise ValueError("Invalid GTFS time")
    return 3600 * h + 60 * m + s


def windows(path, service_date, available_at, prediction_time):
    with zipfile.ZipFile(path) as archive:

        def table(name):
            if name not in archive.namelist():
                return []
            return list(
                csv.DictReader(io.StringIO(archive.read(name).decode("utf-8-sig")))
            )

        if table("frequencies.txt"):
            raise ValueError("Frequency-based GTFS requires explicit expansion")
        day = service_date.strftime("%Y%m%d")
        weekday = service_date.strftime("%A").lower()
        active = {
            r["service_id"]
            for r in table("calendar.txt")
            if r["start_date"] <= day <= r["end_date"] and r[weekday] == "1"
        }
        for r in table("calendar_dates.txt"):
            if r["date"] == day:
                if r["exception_type"] == "1":
                    active.add(r["service_id"])
                else:
                    active.discard(r["service_id"])
        lines = {
            r["route_id"]: r["route_short_name"]
            for r in table("routes.txt")
            if r["route_type"] == "1"
        }
        trips = {
            r["trip_id"]: lines[r["route_id"]]
            for r in table("trips.txt")
            if r["service_id"] in active and r["route_id"] in lines
        }
        stops = {r["stop_id"]: r.get("stop_name", r["stop_id"]) for r in table("stops.txt")}
        visits = []
        for r in table("stop_times.txt"):
            if r["trip_id"] in trips:
                value = r.get("arrival_time") or r.get("departure_time")
                if value and r.get("stop_id") in stops:
                    visits.append((trips[r["trip_id"]], stops[r["stop_id"]], seconds(value), r["trip_id"]))
        noon = datetime.combine(service_date, datetime.min.time()).replace(
            hour=12, tzinfo=ZoneInfo("America/Toronto")
        )
        origin = noon.astimezone(timezone.utc) - timedelta(hours=12)
        grouped = {}
        for line, station, second, trip in visits:
            moment = origin + timedelta(seconds=second)
            hour = moment.replace(minute=0, second=0, microsecond=0)
            grouped.setdefault((line, station, hour), set()).add(trip)
        return [
            {
                "line_id": line,
                "station": station,
                "start": start.isoformat(),
                "end": (start + timedelta(hours=1)).isoformat(),
                "hour": start.astimezone(ZoneInfo("America/Toronto")).hour,
                "date": start.astimezone(ZoneInfo("America/Toronto"))
                .date()
                .isoformat(),
                "scheduled_stop_visits": len(ids),
                "schedule_available_at": available_at,
                "prediction_time": prediction_time,
                "label": None,
                "available_at": None,
                "coverage_verified": False,
            }
            for (line, station, start), ids in sorted(grouped.items())
            if start >= datetime.fromisoformat(prediction_time)
        ]


def label_windows(candidates, events, coverage):
    """Coverage ledger entries need a reviewed reference and publication cutoff."""
    output = []
    for candidate in candidates:
        row = dict(candidate)
        evidence = coverage.get(row["date"], {})
        if evidence.get("verified") and evidence.get("reference"):
            row["coverage_verified"] = True
            row["available_at"] = evidence["available_at"]
            row["label"] = int(
                any(
                    e["line_id"] == row["line_id"]
                    and e.get("station") == row["station"]
                    and datetime.fromisoformat(row["start"])
                    <= datetime.fromisoformat(e["event_time"])
                    < datetime.fromisoformat(row["end"])
                    for e in events
                )
            )
        output.append(row)
    return output
