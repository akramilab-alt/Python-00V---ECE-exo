from datetime import date, datetime
import pytest
from helpers import solo
from modeles import Artist


def test_cancel_removes_the_performance(festival):
    festival.cancel_performance("grand-casino-2027-06-10-2030")

    assert festival.performances == []


def test_cancel_unknown_performance_is_refused(festival):
    with pytest.raises(ValueError, match="Unknown performance"):
        festival.cancel_performance("nope")


def test_the_list_of_performances_is_a_copy(festival):
    # Personne ne peut contourner add_performance en modifiant la liste.
    festival.performances.append("n'importe quoi")

    assert len(festival.performances) == 1


def test_programme_of_a_day_is_sorted(festival):
    festival.add_performance(solo(datetime(2027, 6, 10, 10, 0), venue="la-cabane"))

    starts = [p.start for p in festival.programme(day=date(2027, 6, 10))]

    assert starts == sorted(starts)
    assert len(starts) == 2


def test_programme_filters_by_venue(festival):
    festival.add_performance(solo(datetime(2027, 6, 10, 10, 0), venue="la-cabane"))

    titles = [p.title for p in festival.programme(venue="la-cabane")]

    assert titles == ["Test Solo"]


def test_now_playing_and_up_next(festival):
    festival.add_performance(solo(datetime(2027, 6, 11, 20, 0)))

    during = datetime(2027, 6, 10, 21, 0)

    assert [p.title for p in festival.now_playing(during)] == ["Opening Gala"]
    assert [p.title for p in festival.up_next(during)] == ["Test Solo"]


def test_up_next_gives_three_at_most(festival):
    for hour in (10, 12, 14, 16):
        festival.add_performance(solo(datetime(2027, 6, 11, hour, 0)))

    assert len(festival.up_next(datetime(2027, 6, 10, 21, 0))) == 3


def test_performances_of_an_artist_includes_acts(festival):
    assert len(festival.performances_of("nora-lebrun")) == 1
    assert festival.performances_of("sacha-diallo") == []


def test_performances_are_ordered_by_start_then_venue(festival):
    a = solo(datetime(2027, 6, 11, 20, 0), venue="la-cabane")
    b = solo(datetime(2027, 6, 11, 20, 0), venue="grand-casino")
    c = solo(datetime(2027, 6, 11, 19, 0), venue="la-cabane")

    assert sorted([a, b, c]) == [c, b, a]


def test_two_artists_with_the_same_slug_are_equal():
    assert Artist("Élodie Marchal") == Artist("Elodie Marchal")
    assert Artist("Élodie Marchal") != Artist("Hugo Lemaire")


def test_str_gives_the_summary(festival):
    assert "Test Festival" in str(festival)
    assert "2 venues, 3 artists, 1 performances" in str(festival)


def test_to_data_then_from_data_gives_the_same_festival(festival):
    from modeles import Festival

    again = Festival.from_data(festival.to_data())

    assert again.to_data() == festival.to_data()