import sys
from datetime import datetime
from pathlib import Path
import pytest

# importer models.py pour test_nv
sys.path.insert(0, str(Path(__file__).parent.parent))

from modeles import Artist, Festival, Performance, Venue


@pytest.fixture
def festival():
    """Un petit festival neuf pour chaque test (rien n'est lu dans le fichier)."""
    festival = Festival(
        "Test Festival",
        "2027-06-10",
        "2027-06-13",
        venues=[
            Venue("Grand Casino", 650, "Seafront"),
            Venue("La Cabane", 40, "Beach"),
        ],
        artists=[
            Artist("Paul Kerbrat"),
            Artist("Nora Lebrun"),
            Artist("Sacha Diallo"),
        ],
    )

    # Un plateau le 10 juin, 20:30-22:30, au Grand Casino.
    festival.add_performance(
        Performance(
            title="Opening Gala",
            kind="lineup",
            venue="grand-casino",
            start=datetime(2027, 6, 10, 20, 30),
            duration_minutes=120,
            host="paul-kerbrat",
            acts=["nora-lebrun"],
        )
    )

    return festival