import json
import sys
from datetime import datetime
from festival import load_festival, save_festival
from modeles import Festival, Performance


def load():
    return Festival.from_data(load_festival())


def save(festival):
    save_festival(festival.to_data())


def venue_name(festival, performance):
    venue = festival.find_venue(performance.venue)
    return venue.name if venue else performance.venue


def format_performance(festival, performance):
    return (
        f"{performance.start:%H:%M}-{performance.end:%H:%M} | "
        f"{venue_name(festival, performance)} | "
        f"{performance.title} "
        f"({performance.kind})"
    )

# Commandes

def print_summary(festival):
    print(festival)


def print_venues(festival):
    total_capacity = 0

    for venue in festival.venues:
        print(f"{venue.slug}: {venue.name}, {venue.capacity} seats")
        total_capacity += venue.capacity

    print(f"Total: {total_capacity} seats")


def print_programme(festival, day):
    performances = [
        p for p in festival.programme() if str(p.festival_day) == day
    ]

    if not performances:
        print(f"No performance on '{day}'.")
        return

    date = datetime.fromisoformat(day)

    print(f"Programme for {date:%A %d %B}:")

    for performance in performances:
        print("- " + format_performance(festival, performance))


def role_of(performance, artist_slug):
    if performance.artist == artist_slug:
        return "solo"
    if performance.host == artist_slug:
        return "host"
    if performance.teacher == artist_slug:
        return "teacher"
    return "act"


def print_artist(festival, artist_slug):
    artist = festival.find_artist(artist_slug)

    if artist is None:
        print(f"No artist '{artist_slug}'.")
        return

    print(artist.name)

    for performance in festival.performances_of(artist_slug):
        print(
            f"{performance.start:%Y-%m-%dT%H:%M} | "
            f"{venue_name(festival, performance)} | "
            f"{performance.title} "
            f"({role_of(performance, artist_slug)})"
        )


def print_now(festival, current_time):
    now = datetime.fromisoformat(current_time)

    print(f"On stage at {now:%Y-%m-%d %H:%M}:")

    for performance in festival.now_playing(now):
        print(
            f"- {performance.title} at {venue_name(festival, performance)}, "
            f"until {performance.end:%H:%M}"
        )

    print("Up next:")

    for performance in festival.up_next(now, count=None):
        print("- " + format_performance(festival, performance))


def add_performance(festival):
    title = input("Title: ").strip()
    artist_slug = input("Artist (slug): ").strip()
    venue_slug = input("Venue (slug): ").strip()
    start_text = input("Start (YYYY-MM-DDTHH:MM): ").strip()
    duration_text = input("Duration (minutes): ").strip()

    try:
        start = datetime.fromisoformat(start_text)
    except ValueError:
        raise ValueError(
            f"'{start_text}' is not a valid date. Use YYYY-MM-DDTHH:MM."
        )

    try:
        duration = int(duration_text)
    except ValueError:
        raise ValueError(f"'{duration_text}' is not a number of minutes.")

    performance = Performance(
        title=title,
        kind="solo",
        venue=venue_slug,
        start=start,
        duration_minutes=duration,
        artist=artist_slug,
        min_age=0,
    )

    festival.add_performance(performance)   # toutes les règles sont là
    save(festival)

    print(f"Added: {performance.id}")


def cancel_performance(festival, performance_id):
    performance = festival.cancel_performance(performance_id)
    save(festival)

    print(f"Cancelled: {performance.title}")


def print_help():
    print("Usage:")
    print("  uv run main.py")
    print("  uv run main.py venues")
    print("  uv run main.py programme YYYY-MM-DD")
    print("  uv run main.py artist ARTIST-SLUG")
    print("  uv run main.py now YYYY-MM-DDTHH:MM")
    print("  uv run main.py add")
    print("  uv run main.py cancel ID")

# main

def main():
    try:
        festival = load()

        if len(sys.argv) == 1:
            print_summary(festival)

        elif sys.argv[1] == "venues":
            print_venues(festival)

        elif sys.argv[1] == "programme":
            if len(sys.argv) < 3:
                raise ValueError("Missing date. Use programme YYYY-MM-DD.")

            print_programme(festival, sys.argv[2])

        elif sys.argv[1] == "artist":
            if len(sys.argv) < 3:
                raise ValueError(
                    "Missing artist slug. Use artist ARTIST-SLUG."
                )

            print_artist(festival, sys.argv[2])

        elif sys.argv[1] == "now":
            if len(sys.argv) < 3:
                raise ValueError("Missing time. Use now YYYY-MM-DDTHH:MM.")

            print_now(festival, sys.argv[2])

        elif sys.argv[1] == "add":
            add_performance(festival)

        elif sys.argv[1] == "cancel":
            if len(sys.argv) < 3:
                raise ValueError(
                    "Missing performance ID. Use cancel ID."
                )

            cancel_performance(festival, sys.argv[2])

        else:
            print_help()

    except json.JSONDecodeError:
        print("Error: The festival data file contains invalid JSON.")
        sys.exit(1)

    except FileNotFoundError:
        print("Error: The festival data file was not found.")
        sys.exit(1)

    except ValueError as error:
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()