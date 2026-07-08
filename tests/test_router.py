# tests/test_router.py
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from router import classifier_difficulte, est_tache_code, choisir_modele


def test_question_courte_est_facile():
    assert classifier_difficulte("Salut") == "FACILE"

def test_pourquoi_seul_reste_facile():
    assert classifier_difficulte("Pourquoi il pleut ?") == "FACILE"

def test_detection_code():
    assert est_tache_code("Corrige ce bug Python") == True
    assert est_tache_code("Quelle est la capitale du Niger ?") == False

def test_choix_modele_code():
    modele = choisir_modele("Écris une fonction Python")
    assert "kimi" in modele

def test_choix_modele_general():
    modele = choisir_modele("Quelle est la capitale du Niger ?")
    assert "minimax" in modele


if __name__ == "__main__":
    test_question_courte_est_facile()
    test_pourquoi_seul_reste_facile()
    test_detection_code()
    test_choix_modele_code()
    test_choix_modele_general()
    print("✅ Tous les tests sont passés !")