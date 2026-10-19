import json
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path


DATA_FILE = Path(__file__).parent / "data" / "festival.json"

# Données

def load_festival():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_festival(festival):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(festival, file, ensure_ascii=False, indent=2)

# Slug ------------------

def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()

    result = ""

    for char in text:
        if char.isalnum():
            result += char
        else:
            result += "-"

    return result.strip("-")

# Dates et heures

def start_of(performance):
    return datetime.fromisoformat(performance["start"])


def end_of(performance):
    return start_of(performance) + timedelta(
        minutes=performance["duration_minutes"]
    )


def festival_day(performance):
    return (
        start_of(performance) - timedelta(hours=6)
    ).date()


def format_performance(performance, venue_names):
    start = start_of(performance)
    end = end_of(performance)

    venue = venue_names.get(
        performance["venue"],
        performance["venue"]
    )

    return (
        f"{start:%H:%M}-{end:%H:%M} | "
        f"{venue} | "
        f"{performance['title']} "
        f"({performance['kind']})"
    )


def find_venue(festival, slug):
    for venue in festival["venues"]:
        if slugify(venue["name"]) == slug:
            return venue

    return None


def find_artist(festival, slug):
    for artist in festival["artists"]:
        if slugify(artist["name"]) == slug:
            return artist

    return None


def performance_duration(performance):
    if "duration_minutes" in performance:
        return int(performance["duration_minutes"])

    if "duration" in performance:
        return int(performance["duration"])

    if "end" in performance:
        start = datetime.fromisoformat(performance["start"])
        end = datetime.fromisoformat(performance["end"])
        return int((end - start).total_seconds() // 60)

    raise ValueError(
        f"Cannot determine the duration of '{performance['title']}'."
    )


def performance_artists(performance):
    artists = set()

    for role in ("artist", "host", "teacher"):
        artist = performance.get(role)
        if artist:
            artists.add(artist)

    artists.update(performance.get("acts", []))

    return artists


def check_performance(festival, title, artist_slug, venue_slug, start, duration):
    try:
        start = datetime.fromisoformat(start)
    except ValueError:
        raise ValueError(
            f"'{start}' is not a valid date. Use YYYY-MM-DDTHH:MM."
        )

    try:
        duration = int(duration)
    except ValueError:
        raise ValueError(
            f"'{duration}' is not a number of minutes."
        )

    if not 1 <= duration <= 360:
        raise ValueError("Duration must be between 1 and 360 minutes.")

    venues = {
        slugify(venue["name"]): venue
        for venue in festival["venues"]
    }

    artists = {
        slugify(artist["name"]): artist
        for artist in festival["artists"]
    }

    if venue_slug not in venues:
        raise ValueError(f"Unknown venue '{venue_slug}'.")

    if artist_slug not in artists:
        raise ValueError(f"Unknown artist '{artist_slug}'.")

    festival_start = datetime.fromisoformat(festival["first_day"]).date()
    festival_end = datetime.fromisoformat(festival["last_day"]).date()

    if not festival_start <= start.date() <= festival_end:
        raise ValueError(
            f"{start.date()} is not a day of the festival."
        )

    new_end = start + timedelta(minutes=duration)

    for performance in festival["performances"]:
        existing_start = datetime.fromisoformat(performance["start"])
        existing_duration = performance_duration(performance)
        existing_end = existing_start + timedelta(minutes=existing_duration)

        # réservations du même lieu.
        if performance["venue"] == venue_slug:
            gap = timedelta(minutes=30)

            if (
                start < existing_end + gap
                and existing_start < new_end + gap
            ):
                existing_venue = venues[venue_slug]["name"]
                raise ValueError(
                    f"{existing_venue} is busy with "
                    f"{performance['title']} "
                    f"({existing_start:%Y-%m-%d %H:%M}-"
                    f"{existing_end:%H:%M})."
                )

        # les artistes déjà dans un spectacle
        if artist_slug in performance_artists(performance):
            gap = timedelta(minutes=30)

            if (
                start < existing_end + gap
                and existing_start < new_end + gap
            ):
                raise ValueError(
                    f"{artists[artist_slug]['name']} is on stage "
                    f"in {performance['title']}."
                )

# Données pour l'API 

def festival_days(festival):
    first = date.fromisoformat(festival["first_day"])
    last = date.fromisoformat(festival["last_day"])

    return [
        str(first + timedelta(days=i))
        for i in range((last - first).days + 1)
    ]


def festival_info(festival):
    return {
        "name": festival["name"],
        "first_day": festival["first_day"],
        "last_day": festival["last_day"],
        "days": festival_days(festival),
    }


def venues_list(festival):
    return [
        {"slug": slugify(venue["name"]), **venue}
        for venue in festival["venues"]
    ]


def artists_list(festival):
    artists = [
        {"slug": slugify(artist["name"]), **artist}
        for artist in festival["artists"]
    ]

    return sorted(artists, key=lambda artist: artist["slug"])