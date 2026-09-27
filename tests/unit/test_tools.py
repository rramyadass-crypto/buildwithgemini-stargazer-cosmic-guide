# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from app.agent import (
    find_nearby_places,
    generate_astrophotography_image,
    geocode_address,
    get_iss_location,
    get_near_earth_asteroids,
)


def test_get_iss_location() -> None:
    result = get_iss_location()
    assert "International Space Station" in result
    assert "Coordinates" in result
    assert "Altitude" in result


def test_get_near_earth_asteroids() -> None:
    result = get_near_earth_asteroids()
    assert isinstance(result, str)
    assert "Near-Earth Objects" in result



def test_geocode_address() -> None:
    result = geocode_address("1600 Amphitheatre Pkwy, Mountain View, CA")
    assert isinstance(result, str)
    assert len(result) > 0


def test_find_nearby_places() -> None:
    result = find_nearby_places(37.7749, -122.4194, "park", 1000.0)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_astrophotography_image() -> None:
    result = await generate_astrophotography_image("Crab Nebula M1")
    assert isinstance(result, str)
    assert "https://storage.googleapis.com/" in result
    assert "stargazer-cosmic-guide-qwiklabs-gcp-01-33c05f9db6da" in result


