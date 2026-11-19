def test_formations_catalog_endpoint(client):
    """Vérifie le catalogue des formations issues du diagramme de classe."""
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


def test_formation_detail_endpoint(client):
    """Vérifie le détail d'une formation."""
    res = client.get("/api/v1/formations/1")
    assert res.status_code == 200
    formation = res.json()
    assert formation["id"] == 1
    assert "nom" in formation
