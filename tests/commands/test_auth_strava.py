import fitler.commands.auth_strava as auth_strava


def test_auth_strava_calls_oauth2(monkeypatch):
    called = {}

    def fake_strava_oauth2(client_id, client_secret):
        called["called"] = True
        return {"access_token": "fake_token"}

    monkeypatch.setattr(auth_strava.stravaio, "strava_oauth2", fake_strava_oauth2)
    monkeypatch.setattr(
        "os.environ", {"STRAVA_CLIENT_ID": "id", "STRAVA_CLIENT_SECRET": "secret"}
    )

    auth_strava.run()
    assert called.get("called") is True
