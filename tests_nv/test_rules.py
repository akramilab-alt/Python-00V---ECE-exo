from datetime import date, datetime
import pytest
from helpers import solo

# --- Lieu occupé -------------------------------------------------------

def test_venue_busy_is_refused(festival):
    with pytest.raises(ValueError, match="busy"):
        festival.add_performance(solo(datetime(2027, 6, 10, 21, 0)))


def test_venue_needs_30_minutes_between_shows(festival):
    # Le gala finit à 22:30 : 22:59 est trop tôt, 23:00 est accepté.
    with pytest.raises(ValueError, match="busy"):
        festival.add_performance(solo(datetime(2027, 6, 10, 22, 59)))

    festival.add_performance(solo(datetime(2027, 6, 10, 23, 0)))


# --- Artiste occupé ----------------------------------------------------

def test_artist_busy_in_another_venue(festival):
    # Paul Kerbrat anime le gala (Grand Casino) : il ne peut pas être ailleurs.
    new = solo(datetime(2027, 6, 10, 21, 0), venue="la-cabane", artist="paul-kerbrat")

    with pytest.raises(ValueError, match="on stage"):
        festival.add_performance(new)


def test_artist_busy_as_act_of_a_lineup(festival):
    # Nora Lebrun est invitée du gala : même règle.
    new = solo(datetime(2027, 6, 10, 21, 0), venue="la-cabane", artist="nora-lebrun")

    with pytest.raises(ValueError, match="on stage"):
        festival.add_performance(new)


# --- Jours du festival -------------------------------------------------

def test_show_at_1am_belongs_to_the_previous_day(festival):
    late = solo(datetime(2027, 6, 14, 1, 0))

    assert late.festival_day == date(2027, 6, 13)

    festival.add_performance(late)   # le 13 est un jour du festival : accepté


def test_day_before_the_festival_is_refused(festival):
    # 01:00 le 10 juin appartient au 9 juin : avant le festival.
    with pytest.raises(ValueError, match="not a day"):
        festival.add_performance(solo(datetime(2027, 6, 10, 1, 0)))


def test_day_outside_the_festival_is_refused(festival):
    with pytest.raises(ValueError, match="not a day"):
        festival.add_performance(solo(datetime(2027, 6, 20, 20, 0)))


# --- Durée -------------------------------------------------------------

@pytest.mark.parametrize("duration", [0, 361])
def test_invalid_duration_is_refused(festival, duration):
    with pytest.raises(ValueError, match="Duration"):
        festival.add_performance(solo(datetime(2027, 6, 12, 20, 0), duration=duration))


@pytest.mark.parametrize("duration", [1, 360])
def test_limit_durations_are_accepted(festival, duration):
    festival.add_performance(solo(datetime(2027, 6, 12, 20, 0), duration=duration))


# --- Lieu ou artiste inconnu -------------------------------------------

def test_unknown_venue_is_refused(festival):
    with pytest.raises(ValueError, match="Unknown venue"):
        festival.add_performance(solo(datetime(2027, 6, 12, 20, 0), venue="nowhere"))


def test_unknown_artist_is_refused(festival):
    with pytest.raises(ValueError, match="Unknown artist"):
        festival.add_performance(solo(datetime(2027, 6, 12, 20, 0), artist="nobody"))


# --- Un refus ne change rien -------------------------------------------

def test_refused_show_is_not_added(festival):
    before = len(festival.performances)

    with pytest.raises(ValueError):
        festival.add_performance(solo(datetime(2027, 6, 10, 21, 0)))

    assert len(festival.performances) == before