"""Test scoring service"""
import pytest
from app.services.scoring import ScoringService


@pytest.fixture
def scoring_service():
    """Scoring service fixture"""
    return ScoringService()


def test_altitude_score_low(scoring_service: ScoringService):
    """Test low altitude scoring"""
    score = scoring_service._calculate_altitude_score(20)
    assert 0 <= score <= 40


def test_altitude_score_medium(scoring_service: ScoringService):
    """Test medium altitude scoring"""
    score = scoring_service._calculate_altitude_score(45)
    assert 40 < score < 50


def test_altitude_score_high(scoring_service: ScoringService):
    """Test high altitude scoring"""
    score = scoring_service._calculate_altitude_score(70)
    assert score == 50


def test_brightness_score_bright(scoring_service: ScoringService):
    """Test bright object scoring"""
    score = scoring_service._calculate_brightness_score(1.5)
    assert score == 30


def test_brightness_score_faint(scoring_service: ScoringService):
    """Test faint object scoring"""
    score = scoring_service._calculate_brightness_score(9.0)
    assert score == 5


def test_fov_score_ideal(scoring_service: ScoringService):
    """Test ideal FOV match"""
    score = scoring_service._calculate_fov_score(
        target_size=100,
        fov_h=10.0,
        fov_v=6.7
    )
    # Target fits well in frame
    assert score >= 15


def test_fov_score_too_small(scoring_service: ScoringService):
    """Test FOV score when target is too small"""
    score = scoring_service._calculate_fov_score(
        target_size=5,
        fov_h=10.0,
        fov_v=6.7
    )
    assert score <= 10


def test_fov_score_too_large(scoring_service: ScoringService):
    """Test FOV score when target is too large"""
    score = scoring_service._calculate_fov_score(
        target_size=1000,
        fov_h=10.0,
        fov_v=6.7
    )
    assert score <= 5


def test_duration_score_long(scoring_service: ScoringService):
    """Test long duration scoring"""
    score = scoring_service._calculate_duration_score(300)
    assert score == 10


def test_duration_score_short(scoring_service: ScoringService):
    """Test short duration scoring"""
    score = scoring_service._calculate_duration_score(30)
    assert score <= 5


def test_calculate_total_score(scoring_service: ScoringService):
    """Test total score calculation"""
    result = scoring_service.calculate_score(
        max_altitude=60,
        magnitude=3.0,
        target_size=100,
        fov_horizontal=10.0,
        fov_vertical=6.7,
        duration_minutes=180
    )

    assert "total_score" in result
    assert "breakdown" in result
    assert "altitude" in result["breakdown"]
    assert "brightness" in result["breakdown"]
    assert "fov_match" in result["breakdown"]
    assert "duration" in result["breakdown"]
    assert 0 <= result["total_score"] <= 100
