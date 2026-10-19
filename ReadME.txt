## Structure du projet

festival.py : lit et écrit le fichier JSON et contient les règles / conflits d'horaires, dates
models.py : les classes du festival
api.py : les routes web
main.py : la ligne de commande

## Les classes dans modeles.py

Venue : un lieu (nom, capacité, adresse) / slug est calculé à partir du nom

Artist : un artiste (nom, bio, photo) / // // // // //

Performance : un spectacle. Elle garde les données du fichier et calcule :
le end, festival_day, id et places_left, `involves()`
(cet artiste y participe-t-il ?) et `to_view()` (le JSON envoyé au site)

Choix : une seule classe pour les trois types (solo, plateau, atelier). Ils
partagent la plupart des champs ; les autres restent à `None`. C'est simple
mais imparfait : `to_view()` et `summary()` testent `self.kind`. L'étape 09
remplacera ça par une famille de classes.