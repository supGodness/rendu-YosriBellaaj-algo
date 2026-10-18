"""Rendu - Metaheuristiques.

Le programme est volontairement reproductible: aucune bibliotheque externe
n'est necessaire et les graines aleatoires sont fixees dans main().
"""

from __future__ import annotations

import math
import random
from itertools import combinations


# ---------------------------------------------------------------------------
# Exercice 2 - Problematique de transport
# ---------------------------------------------------------------------------

DEMANDES = (4, 5, 8)  # M1, M2, M3
COUTS = ((5, 3, 4), (6, 7, 2))  # D1 puis D2


def cout_transport(x_d1: tuple[int, int, int]) -> int:
    """Cout d'une solution; D2 complete automatiquement les demandes."""
    x_d2 = tuple(d - x for d, x in zip(DEMANDES, x_d1))
    return sum(COUTS[0][j] * x_d1[j] + COUTS[1][j] * x_d2[j] for j in range(3))


def voisins_transport(x: tuple[int, int, int]):
    """Un voisin transfere un container de D1 d'un magasin vers un autre.

    Ainsi les demandes et les quantites des deux depots restent satisfaites.
    """
    for origine, destination in combinations(range(3), 2):
        for a, b in ((origine, destination), (destination, origine)):
            if x[a] > 0 and x[b] < DEMANDES[b]:
                y = list(x)
                y[a] -= 1
                y[b] += 1
                yield tuple(y), (a, b)


def recherche_taboue_transport(iterations: int = 12, taille_tabou: int = 3):
    """Recherche taboue deterministe, avec critere d'aspiration."""
    courant = (4, 4, 0)  # solution faisable de depart pour D1
    meilleur, meilleur_cout = courant, cout_transport(courant)
    tabou: list[tuple[int, int]] = []
    trace = [(0, courant, meilleur_cout)]

    for it in range(1, iterations + 1):
        candidats = []
        for voisin, mouvement in voisins_transport(courant):
            valeur = cout_transport(voisin)
            # Aspiration: un mouvement tabou est autorise s'il bat le meilleur.
            if mouvement not in tabou or valeur < meilleur_cout:
                candidats.append((valeur, voisin, mouvement))
        # Dans ce tres petit voisinage, tous les mouvements peuvent devenir
        # tabous. On relache alors la restriction pour conserver une recherche.
        if not candidats:
            candidats = [(cout_transport(v), v, m) for v, m in voisins_transport(courant)]
        valeur, courant, mouvement = min(candidats, key=lambda z: z[0])
        if valeur < meilleur_cout:
            meilleur, meilleur_cout = courant, valeur
        tabou.append((mouvement[1], mouvement[0]))  # interdit le retour immediat
        if len(tabou) > taille_tabou:
            tabou.pop(0)
        trace.append((it, courant, valeur))
    return meilleur, meilleur_cout, trace


# ---------------------------------------------------------------------------
# Exercice 3 - Problematique du voyageur de commerce
# ---------------------------------------------------------------------------

ARETES = {
    (1, 2): 14, (1, 3): 15, (1, 8): 17,
    (2, 3): 13, (2, 4): 14, (2, 5): 20, (2, 8): 21,
    (3, 4): 11, (3, 5): 21, (3, 6): 17, (3, 7): 9, (3, 8): 9,
    (4, 5): 11, (4, 6): 10, (4, 7): 8, (4, 8): 20,
    (5, 6): 15, (5, 7): 18, (6, 7): 9, (7, 8): 13,
}
VILLE_DEPART = 1


def poids(a: int, b: int) -> int | None:
    return ARETES.get(tuple(sorted((a, b))))


def cout_tour(tour: tuple[int, ...]) -> float:
    """Retourne +inf lorsqu'une arrete du graphe est absente."""
    cout = 0
    for a, b in zip(tour, tour[1:] + tour[:1]):
        d = poids(a, b)
        if d is None:
            return math.inf
        cout += d
    return cout


def voisins_echange(tour: tuple[int, ...]):
    """Echange deux villes, avec la ville 1 maintenue au debut."""
    for i, j in combinations(range(1, len(tour)), 2):
        voisin = list(tour)
        mouvement = tuple(sorted((voisin[i], voisin[j])))
        voisin[i], voisin[j] = voisin[j], voisin[i]
        voisin = tuple(voisin)
        if math.isfinite(cout_tour(voisin)):
            yield voisin, mouvement


def recherche_taboue_tsp(iterations: int = 15, taille_tabou: int = 5):
    courant = (1, 2, 3, 4, 5, 6, 7, 8)
    meilleur, meilleur_cout = courant, cout_tour(courant)
    tabou: list[tuple[int, int]] = []
    trace = [(0, courant, meilleur_cout)]
    for it in range(1, iterations + 1):
        candidats = []
        for voisin, mouvement in voisins_echange(courant):
            valeur = cout_tour(voisin)
            if mouvement not in tabou or valeur < meilleur_cout:
                candidats.append((valeur, voisin, mouvement))
        valeur, courant, mouvement = min(candidats, key=lambda z: z[0])
        if valeur < meilleur_cout:
            meilleur, meilleur_cout = courant, valeur
        tabou.append(mouvement)
        if len(tabou) > taille_tabou:
            tabou.pop(0)
        trace.append((it, courant, valeur))
    return meilleur, meilleur_cout, trace


def recuit_cinq_iterations():
    """Trace demandee: T0=100 et refroidissement empirique T <- T/2.

    Les voisins et tirages beta sont fixes pour rendre le calcul manuscrit
    et l'execution identiques.
    """
    courant = (1, 2, 3, 4, 5, 6, 7, 8)
    meilleur, meilleur_cout = courant, cout_tour(courant)
    temperature = 100.0
    # paires de villes a echanger, puis nombre beta dans [0,1].
    essais = [((2, 3), 0.50), ((4, 5), 0.40), ((4, 6), 0.50),
              ((3, 8), 0.80), ((4, 6), 0.30)]
    trace = []
    for numero, (paire, beta) in enumerate(essais, 1):
        i, j = (courant.index(paire[0]), courant.index(paire[1]))
        candidat = list(courant)
        candidat[i], candidat[j] = candidat[j], candidat[i]
        candidat = tuple(candidat)
        delta = cout_tour(candidat) - cout_tour(courant)
        proba = 1.0 if delta <= 0 else math.exp(-delta / temperature)
        accepte = delta <= 0 or beta < proba
        if accepte:
            courant = candidat
            if cout_tour(courant) < meilleur_cout:
                meilleur, meilleur_cout = courant, cout_tour(courant)
        trace.append((numero, temperature, candidat, cout_tour(candidat), delta,
                      proba, beta, accepte, courant))
        temperature /= 2
    return meilleur, meilleur_cout, trace


def croisement_ordre(pere: tuple[int, ...], mere: tuple[int, ...], a: int, b: int):
    """Croisement a deux coupures avec reparation des doublons (cours)."""
    enfant: list[int | None] = [None] * len(pere)
    enfant[a:b] = pere[a:b]
    manquantes = [ville for ville in mere if ville not in enfant]
    for indice in list(range(0, a)) + list(range(b, len(pere))):
        enfant[indice] = manquantes.pop(0)
    return tuple(enfant)  # type: ignore[return-value]


def algorithme_genetique(taille_population: int = 40, generations: int = 250,
                         proba_mutation: float = 0.05, graine: int = 7):
    """AG: selection roulette, elitisme, croisement et mutation par echange."""
    alea = random.Random(graine)

    def aleatoire_faisable():
        while True:
            reste = list(range(2, 9))
            alea.shuffle(reste)
            individu = (1, *reste)
            if math.isfinite(cout_tour(individu)):
                return individu

    population = [aleatoire_faisable() for _ in range(taille_population)]
    meilleur = min(population, key=cout_tour)
    historique = [(0, meilleur, cout_tour(meilleur))]

    for generation in range(1, generations + 1):
        # Fitness elevee = tour court; le meilleur est preserve (elitisme).
        fitness = [1 / cout_tour(individu) for individu in population]
        suivante = [min(population, key=cout_tour)]
        while len(suivante) < taille_population:
            pere, mere = alea.choices(population, weights=fitness, k=2)
            a, b = sorted(alea.sample(range(1, 8), 2))
            enfant = croisement_ordre(pere, mere, a, b)
            if alea.random() < proba_mutation:
                i, j = alea.sample(range(1, 8), 2)
                enfant = list(enfant)
                enfant[i], enfant[j] = enfant[j], enfant[i]
                enfant = tuple(enfant)
            # Un enfant avec une arrete absente est remplace, pour rester faisable.
            suivante.append(enfant if math.isfinite(cout_tour(enfant)) else aleatoire_faisable())
        population = suivante
        candidat = min(population, key=cout_tour)
        if cout_tour(candidat) < cout_tour(meilleur):
            meilleur = candidat
        historique.append((generation, meilleur, cout_tour(meilleur)))
    return meilleur, cout_tour(meilleur), historique


if __name__ == "__main__":
    x, valeur, _ = recherche_taboue_transport()
    print("Transport - meilleure livraison D1:", x, "D2:", tuple(d - z for d, z in zip(DEMANDES, x)), "cout:", valeur)
    tour, valeur, _ = recherche_taboue_tsp()
    print("PVC tabou:", tour, "cout:", valeur)
    tour, valeur, _ = recuit_cinq_iterations()
    print("PVC recuit (meilleur memorise):", tour, "cout:", valeur)
    tour, valeur, _ = algorithme_genetique()
    print("PVC genetique:", tour, "cout:", valeur)
