from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from festival import slugify

KINDS = ("solo", "lineup", "workshop")

GAP = timedelta(minutes=30)   # temps de battement entre deux spectacles
MAX_DURATION = 360            # minutes


@dataclass
class Venue:
    name: str
    capacity: int
    address: str

    @property
    def slug(self):
        return slugify(self.name)

    def to_view(self):
        return {
            "slug": self.slug,
            "name": self.name,
            "capacity": self.capacity,
            "address": self.address,
        }

    def to_data(self):
        """Le dictionnaire tel qu'il est écrit dans le fichier."""
        return {
            "name": self.name,
            "capacity": self.capacity,
            "address": self.address,
        }


@dataclass
class Artist:
    name: str
    bio: str = ""
    photo_url: str = ""

    @property
    def slug(self):
        return slugify(self.name)

    # Deux artistes sont les mêmes quand ils ont le même slug.
    def __eq__(self, other):
        if not isinstance(other, Artist):
            return NotImplemented
        return self.slug == other.slug

    def __hash__(self):
        return hash(self.slug)

    def to_view(self):
        return {
            "slug": self.slug,
            "name": self.name,
            "bio": self.bio,
            "photo_url": self.photo_url,
        }

    def to_data(self):
        return {
            "name": self.name,
            "bio": self.bio,
            "photo_url": self.photo_url,
        }


@dataclass
class Performance:
    # Champs communs aux trois types de spectacles
    title: str
    kind: str
    venue: str  # slug du lieu
    start: datetime
    duration_minutes: int
    description: str = ""

    # Plateau (lineup)
    host: str | None = None
    acts: list = field(default_factory=list)

    # Solo
    artist: str | None = None
    min_age: int | None = None

    # Atelier (workshop)
    teacher: str | None = None
    max_participants: int | None = None
    participants: list = field(default_factory=list)

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"Unknown kind '{self.kind}'.")

        if self.duration_minutes <= 0:
            raise ValueError(
                f"'{self.title}': duration must be positive."
            )

    # Ordre des spectacles : par début, puis par lieu.
    # (le slug du lieu remplace son nom : il en est dérivé)
    def __lt__(self, other):
        if not isinstance(other, Performance):
            return NotImplemented
        return (self.start, self.venue) < (other.start, other.venue)

    # --- Calculs ---------------------------------------------------

    @property
    def end(self):
        return self.start + timedelta(minutes=self.duration_minutes)

    @property
    def festival_day(self):
        # Une soirée qui finit après minuit appartient au jour d'avant.
        return (self.start - timedelta(hours=6)).date()

    @property
    def id(self):
        return f"{self.venue}-{self.start:%Y-%m-%d-%H%M}"

    @property
    def places_left(self):
        if self.kind != "workshop":
            return None
        return self.max_participants - len(self.participants)

    # --- Artistes --------------------------------------------------

    def artist_slugs(self):
        """Les slugs des artistes, dans l'ordre : animateur/artiste/prof, puis les invités."""
        slugs = []

        for slug in (self.host, self.artist, self.teacher):
            if slug:
                slugs.append(slug)

        slugs.extend(self.acts)
        return slugs

    def involves(self, artist_slug):
        return artist_slug in self.artist_slugs()

    # --- Vues et fichier -------------------------------------------

    def to_view(self, venues_by_slug, artists_by_slug):
        venue = venues_by_slug[self.venue]

        artists = [
            {"slug": slug, "name": artists_by_slug[slug].name}
            for slug in self.artist_slugs()
        ]

        view = {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "venue": self.venue,
            "venue_name": venue.name,
            "start": self.start.isoformat(timespec="minutes"),
            "end": self.end.isoformat(timespec="minutes"),
            "duration_minutes": self.duration_minutes,
            "festival_day": str(self.festival_day),
            "description": self.description,
            "summary": self.summary(artists_by_slug),
            "capacity": venue.capacity,
            "artists": artists,
        }

        # Les champs propres à chaque type (voir 'Performance' dans API.md).
        if self.kind == "lineup":
            view["host"] = self.host
            view["acts"] = self.acts
        elif self.kind == "solo":
            view["artist"] = self.artist
            view["min_age"] = self.min_age
        elif self.kind == "workshop":
            view["teacher"] = self.teacher
            view["max_participants"] = self.max_participants
            view["participants"] = self.participants
            view["places_left"] = self.places_left

        return view

    def summary(self, artists_by_slug):
        # Le format du plateau vient de la fiche ; les deux autres sont libres.
        if self.kind == "lineup":
            host = artists_by_slug[self.host].name
            acts = ", ".join(artists_by_slug[slug].name for slug in self.acts)
            return f"hosted by {host}, with {acts}"

        if self.kind == "solo":
            return f"{artists_by_slug[self.artist].name}"

        return f"with {artists_by_slug[self.teacher].name}"

    def to_data(self):
        """Le dictionnaire tel qu'il est écrit dans le fichier."""
        data = {
            "kind": self.kind,
            "title": self.title,
            "venue": self.venue,
            "start": self.start.isoformat(timespec="minutes"),
            "duration_minutes": self.duration_minutes,
            "description": self.description,
        }

        if self.kind == "lineup":
            data["host"] = self.host
            data["acts"] = self.acts
        elif self.kind == "solo":
            data["artist"] = self.artist
            data["min_age"] = self.min_age
        else:
            data["teacher"] = self.teacher
            data["max_participants"] = self.max_participants
            data["participants"] = self.participants

        return data


def _as_date(value):
    return date.fromisoformat(value) if isinstance(value, str) else value


def _clash(first, second):
    """Deux spectacles se gênent s'ils se chevauchent, battement de 30 min compris."""
    return (
        first.start < second.end + GAP
        and second.start < first.end + GAP
    )


class Festival:
    """Le festival : il garde les lieux, les artistes et le programme, et ses règles.

    On n'ajoute un spectacle qu'avec add_performance(), qui vérifie tout.
    """

    def __init__(self, name, first_day, last_day, venues=(), artists=()):
        self.name = name
        self.first_day = _as_date(first_day)
        self.last_day = _as_date(last_day)
        self._venues = {venue.slug: venue for venue in venues}
        self._artists = {artist.slug: artist for artist in artists}
        self._performances = []

    @classmethod
    def from_data(cls, data):
        """Construit le festival depuis le dictionnaire du fichier JSON.

        Le fichier est considéré comme fiable : ses spectacles ne sont
        pas revérifiés (seuls les ajouts le sont).
        """
        venues, artists, performances = build_objects(data)

        festival = cls(
            data["name"], data["first_day"], data["last_day"],
            venues, artists,
        )
        festival._performances = list(performances)

        return festival

    def to_data(self):
        """Le dictionnaire à écrire dans le fichier JSON."""
        return {
            "name": self.name,
            "first_day": str(self.first_day),
            "last_day": str(self.last_day),
            "venues": [venue.to_data() for venue in self._venues.values()],
            "artists": [artist.to_data() for artist in self._artists.values()],
            "performances": [p.to_data() for p in self._performances],
        }

    def __str__(self):
        return (
            f"{self.name}\n"
            f"from {self.first_day} to {self.last_day}\n"
            f"{len(self._venues)} venues, "
            f"{len(self._artists)} artists, "
            f"{len(self._performances)} performances"
        )

    # --- Lecture ---------------------------------------------------

    @property
    def venues(self):
        return list(self._venues.values())

    @property
    def artists(self):
        return list(self._artists.values())

    @property
    def performances(self):
        # Une copie : modifier cette liste ne change pas le festival.
        return list(self._performances)

    @property
    def days(self):
        count = (self.last_day - self.first_day).days + 1
        return [self.first_day + timedelta(days=i) for i in range(count)]

    def find_venue(self, slug):
        return self._venues.get(slug)

    def find_artist(self, slug):
        return self._artists.get(slug)

    def find_performance(self, performance_id):
        for performance in self._performances:
            if performance.id == performance_id:
                return performance
        return None

    def programme(self, day=None, venue=None):
        selected = self._performances

        if day is not None:
            selected = [p for p in selected if p.festival_day == day]

        if venue is not None:
            selected = [p for p in selected if p.venue == venue]

        return sorted(selected)

    def performances_of(self, artist_slug):
        return sorted(p for p in self._performances if p.involves(artist_slug))

    def now_playing(self, at):
        return sorted(p for p in self._performances if p.start <= at < p.end)

    def up_next(self, at, count=3):
        return sorted(p for p in self._performances if p.start > at)[:count]

    # --- Écriture (les règles sont ici) ----------------------------

    def add_performance(self, performance):
        self._check(performance)
        self._performances.append(performance)
        return performance

    def cancel_performance(self, performance_id):
        performance = self.find_performance(performance_id)

        if performance is None:
            raise ValueError(f"Unknown performance '{performance_id}'.")

        self._performances.remove(performance)
        return performance

    def _check(self, new):
        if not 1 <= new.duration_minutes <= MAX_DURATION:
            raise ValueError(
                f"Duration must be between 1 and {MAX_DURATION} minutes."
            )

        venue = self._venues.get(new.venue)

        if venue is None:
            raise ValueError(f"Unknown venue '{new.venue}'.")

        for slug in new.artist_slugs():
            if slug not in self._artists:
                raise ValueError(f"Unknown artist '{slug}'.")

        if not self.first_day <= new.festival_day <= self.last_day:
            raise ValueError(
                f"{new.festival_day} is not a day of the festival."
            )

        for other in self._performances:
            if not _clash(new, other):
                continue

            if other.venue == new.venue:
                raise ValueError(
                    f"{venue.name} is busy with {other.title} "
                    f"({other.start:%Y-%m-%d %H:%M}-{other.end:%H:%M})."
                )

            shared = set(new.artist_slugs()) & set(other.artist_slugs())

            if shared:
                name = self._artists[sorted(shared)[0]].name
                raise ValueError(f"{name} is on stage in {other.title}.")


# ------------------------------------------------------------------
# Du fichier JSON vers les objets
# ------------------------------------------------------------------

def build_objects(data):
    """Transforme le dictionnaire du fichier en listes d'objets."""
    venues = [
        Venue(v["name"], v["capacity"], v["address"])
        for v in data["venues"]
    ]

    artists = [
        Artist(a["name"], a.get("bio", ""), a.get("photo_url", ""))
        for a in data["artists"]
    ]

    performances = []

    for p in data["performances"]:
        performances.append(
            Performance(
                title=p["title"],
                kind=p["kind"],
                venue=p["venue"],
                start=datetime.fromisoformat(p["start"]),
                duration_minutes=p["duration_minutes"],
                description=p.get("description", ""),
                host=p.get("host"),
                acts=p.get("acts", []),
                artist=p.get("artist"),
                min_age=p.get("min_age"),
                teacher=p.get("teacher"),
                max_participants=p.get("max_participants"),
                participants=p.get("participants", []),
            )
        )

    return venues, artists, performances