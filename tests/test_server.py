import json
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from arcpuzzles import Catalog
from arcpuzzles.server import make_server


def test_http_filters_errors_and_challenge_match_python(library):
    catalog = Catalog(library)
    with make_server(catalog, port=0) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with urlopen(base + "/v1/puzzles?approved=true&source=training&limit=1") as response:
                payload = json.load(response)
            assert payload["items"] == catalog.query(approved=True, source="training", limit=1)
            with urlopen(base + "/v1/puzzles/aaaa00000001/challenge") as response:
                assert json.load(response) == catalog.challenge("aaaa00000001")
            for path, expected in [("/v1/puzzles?approved=maybe", 400), ("/v1/puzzles?unknown=1", 400),
                                   ("/v1/puzzles?limit=-1", 400), ("/v1/puzzles?limit=1001", 400),
                                   ("/v1/puzzles?approved=true&approved=false", 400),
                                   ("/v1/puzzles/missing", 404)]:
                with pytest.raises(HTTPError) as error:
                    urlopen(base + path)
                assert error.value.code == expected
            with pytest.raises(HTTPError) as error:
                urlopen(Request(base + "/v1/puzzles", data=b"{}", method="POST"))
            assert error.value.code == 501
            assert not (library / "REVIEW").exists()
        finally:
            server.shutdown()
            thread.join(timeout=3)
