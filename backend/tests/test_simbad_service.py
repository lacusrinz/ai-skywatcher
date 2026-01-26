import pytest
from unittest.mock import AsyncMock, patch
from app.services.simbad import SIMBADService

@pytest.mark.asyncio
async def test_query_object():
    service = SIMBADService()

    # Mock HTTP response
    mock_response = {
        'data': [{
            'oid': 'M31',
            'main_id': b'M  31',
            'ra': 10.684708,
            'dec': 41.268750,
            'galdim_majaxis': 190.0,
            'galdim_minaxis': 60.0,
            'V': 3.4,
            'all_types': 'G'
        }]
    }

    with patch.object(service, '_execute_tap_query', return_value=mock_response):
        obj = await service.query_object('M31')

    assert obj is not None
    assert obj.id == 'M31'
    assert obj.type == 'GALAXY'
    assert obj.magnitude == 3.4

@pytest.mark.asyncio
async def test_query_object_not_found():
    service = SIMBADService()

    with patch.object(service, '_execute_tap_query', return_value={'data': []}):
        obj = await service.query_object('UNKNOWN')

    assert obj is None

@pytest.mark.asyncio
async def test_extract_number():
    service = SIMBADService()

    assert service._extract_number('M31') == 31
    assert service._extract_number('NGC224') == 224
    assert service._extract_number('IC1234') == 1234

@pytest.mark.asyncio
async def test_map_simbad_type():
    service = SIMBADService()

    assert service._map_simbad_type('G') == 'GALAXY'
    assert service._map_simbad_type('PN') == 'PLANETARY'
    assert service._map_simbad_type('OCl') == 'CLUSTER'
    assert service._map_simbad_type('GCl') == 'CLUSTER'
    assert service._map_simbad_type('HII') == 'NEBULA'
    assert service._map_simbad_type('') == 'NEBULA'
