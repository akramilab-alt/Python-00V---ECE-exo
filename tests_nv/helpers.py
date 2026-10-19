import sys
from pathlib import Path

# models.py est à la racine du projet, un dossier au-dessus.
sys.path.insert(0, str(Path(__file__).parent.parent))

from modeles import Performance


def solo(start, venue="grand-casino", artist="sacha-diallo", duration=60):
    """Fabrique un solo pour les tests."""
    return Performance(
        title="Test Solo",
        kind="solo",
        venue=venue,
        start=start,
        duration_minutes=duration,
        artist=artist,
        min_age=0,
    )