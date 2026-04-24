"""Unit / integration tests for the artwork API endpoints."""
import pytest
from artwork_service.models import Artist, Categories, Artwork



def _seed_artist_and_category(db):
    """Insert one artist + one category and return their IDs."""
    artist = Artist(artist_name="Test", artist_surname="Artist", country="Testland")
    category = Categories(category_name="Painting")
    db.add_all([artist, category])
    db.commit()
    db.refresh(artist)
    db.refresh(category)
    return artist.artist_id, category.category_id


def _seed_artwork(db, artist_id, category_id, **overrides):
    defaults = dict(
        title="Test Art",
        artist_id=artist_id,
        category_id=category_id,
        starting_price=100.0,
        current_price=100.0,
        status="available",
        is_available=True,
    )
    defaults.update(overrides)
    art = Artwork(**defaults)
    db.add(art)
    db.commit()
    db.refresh(art)
    return art



class TestGetArtworks:
    def test_empty_list(self, client):
        resp = client.get("/artworks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_seeded_artworks(self, client, db_session):
        aid, cid = _seed_artist_and_category(db_session)
        _seed_artwork(db_session, aid, cid, title="A")
        _seed_artwork(db_session, aid, cid, title="B")
        resp = client.get("/artworks")
        assert resp.status_code == 200
        titles = {a["title"] for a in resp.json()}
        assert titles == {"A", "B"}



class TestGetArtworkById:
    def test_not_found(self, client):
        resp = client.get("/artworks/999")
        assert resp.status_code == 404

    def test_found(self, client, db_session):
        aid, cid = _seed_artist_and_category(db_session)
        art = _seed_artwork(db_session, aid, cid, title="Found Me")
        resp = client.get(f"/artworks/{art.artwork_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Found Me"



class TestCreateArtwork:
    def test_create_success(self, client, db_session):
        aid, cid = _seed_artist_and_category(db_session)
        payload = {
            "title": "New Masterpiece",
            "artist_id": aid,
            "category_id": cid,
            "starting_price": 500.0,
            "current_price": 500.0,
        }
        resp = client.post("/artworks", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "New Masterpiece"
        assert body["artwork_id"] is not None

    def test_create_with_status(self, client, db_session):
        aid, cid = _seed_artist_and_category(db_session)
        payload = {
            "title": "Auctioned",
            "artist_id": aid,
            "category_id": cid,
            "starting_price": 200.0,
            "current_price": 300.0,
            "status": "on_auction",
        }
        resp = client.post("/artworks", json=payload)
        assert resp.status_code == 201
        assert resp.json()["status"] == "on_auction"


class TestUpdateArtwork:
    def test_update_title(self, client, db_session):
        aid, cid = _seed_artist_and_category(db_session)
        art = _seed_artwork(db_session, aid, cid, title="Old Title")
        resp = client.put(f"/artworks/{art.artwork_id}", json={"title": "New Title"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    def test_update_nonexistent(self, client):
        resp = client.put("/artworks/999", json={"title": "Nope"})
        assert resp.status_code == 404



class TestUpdateArtworkPrice:
    def test_update_price(self, client, db_session):
        aid, cid = _seed_artist_and_category(db_session)
        art = _seed_artwork(db_session, aid, cid)
        resp = client.put(
            f"/artworks/{art.artwork_id}/price",
            json={"current_price": 999.99},
        )
        assert resp.status_code == 200
        assert resp.json()["current_price"] == 999.99

    def test_price_not_found(self, client):
        resp = client.put("/artworks/999/price", json={"current_price": 1.0})
        assert resp.status_code == 404
