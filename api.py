from datetime import date, datetime

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from festival import load_festival
from modeles import Festival

app = FastAPI()


def get_festival_object() -> Festival:
    """Relit le fichier et construit le festival (un par requête)."""
    return Festival.from_data(load_festival())


def views(festival: Festival, performances) -> list[dict]:
    """Transforme des spectacles en JSON pour le site."""
    venues = {venue.slug: venue for venue in festival.venues}
    artists = {artist.slug: artist for artist in festival.artists}
    return [p.to_view(venues, artists) for p in performances]


# --- Étape 06 -----------------------------------------------------

@app.get("/api/festival")
def get_festival() -> dict:
    festival = get_festival_object()

    return {
        "name": festival.name,
        "first_day": str(festival.first_day),
        "last_day": str(festival.last_day),
        "days": [str(day) for day in festival.days],
    }


@app.get("/api/venues")
def get_venues() -> list[dict]:
    return [venue.to_view() for venue in get_festival_object().venues]


@app.get("/api/artists")
def get_artists() -> list[dict]:
    artists = [artist.to_view() for artist in get_festival_object().artists]
    return sorted(artists, key=lambda artist: artist["slug"])


# --- Étape 07 -----------------------------------------------------

@app.get("/api/programme")
def get_programme(day: date | None = None, venue: str | None = None) -> list[dict]:
    festival = get_festival_object()

    if venue is not None and festival.find_venue(venue) is None:
        raise HTTPException(status_code=404, detail=f"No venue '{venue}'.")

    return views(festival, festival.programme(day=day, venue=venue))


@app.get("/api/performances/{performance_id}")
def get_performance(performance_id: str) -> dict:
    festival = get_festival_object()
    performance = festival.find_performance(performance_id)

    if performance is None:
        raise HTTPException(
            status_code=404, detail=f"No performance '{performance_id}'."
        )

    return views(festival, [performance])[0]


@app.get("/api/artists/{slug}")
def get_artist(slug: str) -> dict:
    festival = get_festival_object()
    artist = festival.find_artist(slug)

    if artist is None:
        raise HTTPException(status_code=404, detail=f"No artist '{slug}'.")

    view = artist.to_view()
    view["performances"] = views(festival, festival.performances_of(slug))

    return view


# --- Étape 08 -----------------------------------------------------

@app.get("/api/now")
def get_now(at: datetime | None = None) -> dict:
    festival = get_festival_object()

    if at is None:
        at = datetime.now()

    return {
        "now_playing": views(festival, festival.now_playing(at)),
        "up_next": views(festival, festival.up_next(at, 3)),
    }


# Toujours en dernier : sinon le site masque les routes ci-dessus.
app.mount("/", StaticFiles(directory="web/public", html=True))