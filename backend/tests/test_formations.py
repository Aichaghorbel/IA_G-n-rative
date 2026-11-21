from datetime import date, timedelta
from app.core.security import create_access_token


def get_auth_headers(subject="1", role="Administrateur", email="admin@smartcampus.tn"):
    token = create_access_token(subject=subject, role=role, email=email)
    return {"Authorization": f"Bearer {token}"}


def test_formations_catalog_endpoint(client):
    """Vérifie le catalogue public des formations (IIT / ISB)."""
    res = client.get("/api/v1/formations")
    assert res.status_code == 200
    formations = res.json()
    assert isinstance(formations, list)
    assert len(formations) > 0
    first = formations[0]
    assert "nom" in first
    assert "universite" in first
    assert "specialites" in first
    assert "tarifs" in first
    assert "equivalences" in first
    assert "statut_publication" in first
    assert first["statut_publication"] == "publie"


def test_formation_detail_endpoint(client):
    """Vérifie la consultation du détail d'une formation."""
    res = client.get("/api/v1/formations/1")
    assert res.status_code == 200
    formation = res.json()
    assert formation["id"] == 1
    assert "nom" in formation
    assert "conditionsAdmission" in formation


def test_required_fields_validation(client):
    """Contrôle des champs obligatoires : renvoie 422 si un champ requis manque."""
    admin_headers = get_auth_headers(role="Administrateur")

    # Manque 'universite' et 'description'
    invalid_data = {
        "nom": "Formation Incomplète"
    }
    res = client.post("/api/v1/formations/", json=invalid_data, headers=admin_headers)
    assert res.status_code == 422


def test_rbac_access_control(client):
    """Contrôle des autorisations d'accès (RBAC) : seul le Responsable peut modifier."""
    new_formation = {
        "nom": "Licence Test RBAC",
        "universite": "ISB",
        "description": "Description de test d'autorisation RBAC.",
        "duree": 3
    }

    # 1. Candidat tente de créer une formation -> Doit être refusé (403)
    candidat_headers = get_auth_headers(subject="4", role="Candidat", email="sarra.benali@gmail.com")
    res_candidat = client.post("/api/v1/formations/", json=new_formation, headers=candidat_headers)
    assert res_candidat.status_code == 403

    # 2. Utilisateur non authentifié -> Doit être refusé (403)
    res_anon = client.post("/api/v1/formations/", json=new_formation)
    assert res_anon.status_code == 403

    # 3. Responsable / Administrateur -> Doit être accepté (201)
    admin_headers = get_auth_headers(role="Administrateur")
    res_admin = client.post("/api/v1/formations/", json=new_formation, headers=admin_headers)
    assert res_admin.status_code == 201

    # Nettoyage
    created_id = res_admin.json()["id"]
    client.delete(f"/api/v1/formations/{created_id}", headers=admin_headers)


def test_crud_formation_lifecycle(client):
    """Cycle de vie complet : Création, Modification, Consultation et Suppression."""
    admin_headers = get_auth_headers(role="Administrateur")

    # 1. Create
    data = {
        "nom": "Mastère Data Science & IA",
        "universite": "IIT",
        "description": "Formation d'excellence en intelligence artificielle.",
        "duree": 2,
        "conditionsAdmission": "Diplôme de Licence scientifique ou d'ingénieur.",
        "statut_publication": "publie"
    }
    create_res = client.post("/api/v1/formations/", json=data, headers=admin_headers)
    assert create_res.status_code == 201
    form_id = create_res.json()["id"]

    # 2. Read
    get_res = client.get(f"/api/v1/formations/{form_id}")
    assert get_res.status_code == 200
    assert get_res.json()["nom"] == "Mastère Data Science & IA"

    # 3. Update (Conditions d'admission modifiées)
    update_data = {
        "conditionsAdmission": "Licence en Informatique mention Bien + Entretien technique obligatoire."
    }
    put_res = client.put(f"/api/v1/formations/{form_id}", json=update_data, headers=admin_headers)
    assert put_res.status_code == 200
    assert "Entretien technique obligatoire" in put_res.json()["conditionsAdmission"]

    # 4. Delete
    del_res = client.delete(f"/api/v1/formations/{form_id}", headers=admin_headers)
    assert del_res.status_code == 204

    # 5. Verify Not Found (404)
    after_del = client.get(f"/api/v1/formations/{form_id}")
    assert after_del.status_code == 404


def test_crud_tarifs_and_modalites(client):
    """Gestion des frais de scolarité et modalités de paiement."""
    admin_headers = get_auth_headers(role="Administrateur")

    # Créer une formation support
    form_res = client.post("/api/v1/formations/", json={
        "nom": "Formation Test Tarifs",
        "universite": "ISB",
        "description": "Description test tarifs.",
        "duree": 3
    }, headers=admin_headers)
    form_id = form_res.json()["id"]

    try:
        # 1. Ajouter un tarif
        tarif_data = {
            "montant_9mois": 5800.0,
            "type": "fraisNational",
            "Annee": "2026-2027",
            "devise": "DT",
            "modalites_paiement": "Comptant à l'inscription ou 3 chèques échelonnés"
        }
        res_t = client.post(f"/api/v1/formations/{form_id}/tarifs", json=tarif_data, headers=admin_headers)
        assert res_t.status_code == 201
        tarif_id = res_t.json()["id"]
        assert res_t.json()["modalites_paiement"] == "Comptant à l'inscription ou 3 chèques échelonnés"

        # 2. Modifier le tarif
        update_t = {
            "montant_9mois": 6000.0,
            "modalites_paiement": "4 tranches bimensuelles"
        }
        res_put = client.put(f"/api/v1/formations/tarifs/{tarif_id}", json=update_t, headers=admin_headers)
        assert res_put.status_code == 200
        assert res_put.json()["montant_9mois"] == 6000.0
        assert res_put.json()["modalites_paiement"] == "4 tranches bimensuelles"

        # 3. Supprimer le tarif
        del_t = client.delete(f"/api/v1/formations/tarifs/{tarif_id}", headers=admin_headers)
        assert del_t.status_code == 204

    finally:
        client.delete(f"/api/v1/formations/{form_id}", headers=admin_headers)


def test_hierarchy_specialite_programme_matiere(client):
    """Gestion hiérarchique : Formation -> Spécialité -> Programme -> Matières."""
    admin_headers = get_auth_headers(role="Administrateur")

    # Formation
    form_res = client.post("/api/v1/formations/", json={
        "nom": "Génie Civil & Environnement",
        "universite": "IIT",
        "description": "Cursus ingénieur en structures et environnement.",
        "duree": 5
    }, headers=admin_headers)
    form_id = form_res.json()["id"]

    try:
        # 1. Spécialité
        spec_res = client.post(f"/api/v1/formations/{form_id}/specialites", json={
            "nom": "Bâtiments & Ouvrages d'Art",
            "description": "Conception parasismique et matériaux innovants."
        }, headers=admin_headers)
        assert spec_res.status_code == 201
        spec_id = spec_res.json()["id"]

        # 2. Programme (Semestre 1)
        prog_res = client.post(f"/api/v1/formations/specialites/{spec_id}/programmes", json={
            "nom": "Tronc Commun Structures",
            "semestre": 1
        }, headers=admin_headers)
        assert prog_res.status_code == 201
        prog_id = prog_res.json()["id"]

        # 3. Matière (Résistance des Matériaux)
        mat_res = client.post(f"/api/v1/formations/programmes/{prog_id}/matieres", json={
            "nom": "Résistance des Matériaux (RDM)",
            "description": "Calculs des contraintes et déformations.",
            "coefficient": 3,
            "volumeHoraire": 60
        }, headers=admin_headers)
        assert mat_res.status_code == 201
        assert mat_res.json()["coefficient"] == 3
        assert mat_res.json()["volumeHoraire"] == 60

        # 4. Vérifier la hiérarchie dans la consultation de la formation
        detail = client.get(f"/api/v1/formations/{form_id}").json()
        assert len(detail["specialites"]) == 1
        assert detail["specialites"][0]["nom"] == "Bâtiments & Ouvrages d'Art"
        assert len(detail["specialites"][0]["programmes"]) == 1
        assert detail["specialites"][0]["programmes"][0]["matieres"][0]["nom"] == "Résistance des Matériaux (RDM)"

    finally:
        client.delete(f"/api/v1/formations/{form_id}", headers=admin_headers)


def test_search_and_filters(client):
    """Recherche plein texte et filtrage multi-critères."""
    # Recherche par université
    res_iit = client.get("/api/v1/formations?universite=IIT")
    assert res_iit.status_code == 200
    for f in res_iit.json():
        assert f["universite"] == "IIT"

    # Recherche par mot-clé
    res_search = client.get("/api/v1/formations?q=Logiciel")
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1
    assert "Logiciel" in res_search.json()[0]["nom"]


def test_publication_and_validity_rule(client):
    """
    Règle Métier :
    - Les candidats et l'IA ne voient QUE les formations 'publie' et valides.
    - Le responsable peut voir les 'brouillon'.
    """
    admin_headers = get_auth_headers(role="Administrateur")
    candidat_headers = get_auth_headers(subject="4", role="Candidat", email="sarra.benali@gmail.com")

    # 1. Le Responsable crée une formation en BROUILLON (pas encore officielle)
    draft_res = client.post("/api/v1/formations/", json={
        "nom": "Formation Secrète Brouillon 2027",
        "universite": "IIT",
        "description": "Formation en cours de conception.",
        "duree": 3,
        "statut_publication": "brouillon"
    }, headers=admin_headers)
    draft_id = draft_res.json()["id"]

    try:
        # 2. Le Responsable consulte avec filtre statut=brouillon -> Il la voit
        admin_list = client.get("/api/v1/formations?statut=brouillon", headers=admin_headers).json()
        assert any(f["id"] == draft_id for f in admin_list)

        # 3. Le Candidat consulte la liste -> La formation brouillon N'APPARAÎT PAS
        cand_list = client.get("/api/v1/formations", headers=candidat_headers).json()
        assert not any(f["id"] == draft_id for f in cand_list)

        # 4. Le Candidat tente d'accéder directement au détail du brouillon -> 404 Not Found
        cand_detail = client.get(f"/api/v1/formations/{draft_id}", headers=candidat_headers)
        assert cand_detail.status_code == 404

        # 5. Le Responsable publie la formation
        client.put(f"/api/v1/formations/{draft_id}", json={"statut_publication": "publie"}, headers=admin_headers)

        # 6. Maintenant le Candidat peut la voir !
        cand_list_after = client.get("/api/v1/formations", headers=candidat_headers).json()
        assert any(f["id"] == draft_id for f in cand_list_after)

    finally:
        client.delete(f"/api/v1/formations/{draft_id}", headers=admin_headers)
