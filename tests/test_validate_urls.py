"""Tests for URL classification and validation (validate_urls.py).

Tests cover all 4 tiers, edge cases (playlists, invalid URLs, unknown domains),
and validate_single output structure.
"""
import pytest
from validate_urls import classify_url, validate_single


# --- Tier 1: Interactive learning platforms ---

class TestTier1:
    def test_exercism_track(self):
        tier, type_name = classify_url("https://exercism.org/tracks/python")
        assert tier == 1
        assert type_name == "exercism track"

    def test_codecademy(self):
        tier, type_name = classify_url("https://codecademy.com/learn/python")
        assert tier == 1
        assert type_name == "codecademy"

    def test_brilliant_course(self):
        tier, type_name = classify_url("https://brilliant.org/courses/math")
        assert tier == 1
        assert type_name == "brilliant course"

    def test_leetcode_study_plan(self):
        tier, type_name = classify_url("https://leetcode.com/studyplan/python")
        assert tier == 1
        assert type_name == "leetcode study plan"


# --- Tier 2: Official courses and docs ---

class TestTier2:
    def test_coursera(self):
        tier, type_name = classify_url("https://coursera.org/learn/python")
        assert tier == 2
        assert type_name == "coursera"

    def test_edx(self):
        tier, type_name = classify_url("https://edx.org/learn/python")
        assert tier == 2
        assert type_name == "edx"

    def test_khan_academy(self):
        tier, type_name = classify_url("https://khanacademy.org/math")
        assert tier == 2
        assert type_name == "khan academy"


# --- Tier 3: YouTube single videos ---

class TestTier3:
    def test_youtube_single_video(self):
        tier, type_name = classify_url("https://youtube.com/watch?v=abc123")
        assert tier == 3
        assert type_name == "YouTube single video"

    def test_youtu_be_short(self):
        tier, type_name = classify_url("https://youtu.be/abc123")
        assert tier == 3
        assert type_name == "YouTube single video"


# --- YouTube playlist rejection ---

class TestYouTubePlaylistRejection:
    def test_youtube_watch_with_list_param(self):
        tier, type_name = classify_url("https://youtube.com/watch?v=abc&list=def")
        assert tier is None
        assert "PLAYLIST" in type_name

    def test_youtube_playlist_endpoint(self):
        tier, type_name = classify_url("https://youtube.com/playlist?list=def")
        assert tier is None
        assert "PLAYLIST" in type_name

    def test_youtube_watch_with_list_and_index(self):
        tier, type_name = classify_url(
            "https://youtube.com/watch?v=abc123&list=PLxyz&index=1"
        )
        assert tier is None
        assert "PLAYLIST" in type_name


# --- Tier 4: Reference ---

class TestTier4:
    def test_wikipedia(self):
        tier, type_name = classify_url("https://wikipedia.org/wiki/Python")
        assert tier == 4
        assert type_name == "wikipedia"

    def test_github_docs(self):
        tier, type_name = classify_url(
            "https://github.com/user/repo/blob/main/file"
        )
        assert tier == 4
        assert type_name == "github wiki/docs"

    def test_medium_article(self):
        tier, type_name = classify_url("https://medium.com/@user/article")
        assert tier == 4
        assert type_name == "medium article"


# --- Edge cases ---

class TestEdgeCases:
    def test_not_a_url(self):
        tier, type_name = classify_url("not-a-url")
        assert tier is None
        assert "Not a valid HTTP URL" in type_name

    def test_ftp_url_rejected(self):
        tier, type_name = classify_url("ftp://example.com")
        assert tier is None
        assert "Not a valid HTTP URL" in type_name

    def test_unknown_domain(self):
        tier, type_name = classify_url("https://unknown-site.example.com/page")
        assert tier is None
        assert "Unknown" in type_name or "untrusted" in type_name


# --- validate_single output structure ---

class TestValidateSingle:
    def test_returns_dict_with_required_keys(self):
        result = validate_single("https://exercism.org/tracks/python")
        assert isinstance(result, dict)
        assert "url" in result
        assert "tier" in result
        assert "type" in result
        assert "valid" in result

    def test_no_http_check_omits_http_keys(self):
        result = validate_single("https://exercism.org/tracks/python", check_http=False)
        assert "http_status" not in result
        assert "http_ok" not in result

    def test_valid_result_set(self):
        result = validate_single("https://exercism.org/tracks/python")
        assert result["valid"] is True
        assert result["tier"] == 1

    def test_invalid_result_set(self):
        result = validate_single("not-a-url")
        assert result["valid"] is False
        assert result["tier"] is None
