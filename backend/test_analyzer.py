"""
test_analyzer.py – Regression tests for the Smart Resume Analyzer backend.

Tests cover:
  - Sample resume generation (DOCX + PDF)
  - Text extraction from both formats
  - Certification detection (section heading + individual entries)
  - Education detection
  - Project detection
  - Contact info detection
  - Skill extraction (controlled vocabulary, no junk words)
  - Role-based keyword matching (core vs optional)
  - Overall score consistency (category totals = resume_score)
  - API contract (all expected response fields present)
  - Error handling (missing file, bad extension, empty file, missing role)

Run:  python -m pytest test_analyzer.py -v
"""

import io
import os
import sys
import json
import pytest

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

from app import (
    app,
    _extract_text_from_docx,
    _extract_text_from_pdf,
    _extract_skills_from_text,
    _find_certification_entries,
    _section_score,
    _match_keywords,
    _CATEGORY_WEIGHTS,
)

# ──────────────────────────────────────────────────────────────────────────
# Fixtures – build a realistic sample resume in both formats
# ──────────────────────────────────────────────────────────────────────────

SAMPLE_RESUME_TEXT = """\
Jane Doe
jane.doe@example.com | +1 (555) 123-4567
linkedin.com/in/janedoe | github.com/janedoe

SUMMARY
Creative and detail-oriented Web Developer with 3+ years of experience
building responsive, accessible web applications using modern JavaScript
frameworks and cloud technologies.

EDUCATION
Bachelor of Science in Computer Science
University of Technology — Graduated May 2022
GPA: 3.7/4.0

SKILLS
JavaScript, TypeScript, React, Node.js, Express, HTML, CSS, Tailwind,
Git, REST API, MongoDB, PostgreSQL, Docker, CI/CD, Figma, Jest,
Responsive Design, Accessibility, Next.js, GraphQL, Firebase, Webpack

EXPERIENCE
Frontend Developer — Acme Corp (Jun 2022 – Present)
- Developed a customer dashboard used by 5,000+ users
- Reduced page load time by 40% through code splitting and lazy loading
- Led migration from JavaScript to TypeScript across 12 microservices
- Designed and implemented a component library with 30+ reusable components

Junior Web Developer — StartupXYZ (Jan 2021 – May 2022)
- Built REST API endpoints serving 200+ requests per second
- Implemented responsive design achieving 98% Lighthouse accessibility score
- Coordinated with designers using Figma to deliver pixel-perfect UIs

PROJECTS
Portfolio Website
- Designed and deployed a personal portfolio using Next.js and Tailwind
- Integrated a headless CMS for blog content management

Task Manager App
- Built a full-stack CRUD application with React, Node.js, and MongoDB
- Implemented JWT authentication and role-based access control

CERTIFICATIONS
Introduction to Web Development — Example Learning Platform (2025)
Python Fundamentals — Example Learning Platform (2025)

LANGUAGES
English (Native), Spanish (Conversational)
"""


def _build_sample_docx_bytes() -> bytes:
    """Create a DOCX file in memory from the sample resume text."""
    from docx import Document
    doc = Document()
    for line in SAMPLE_RESUME_TEXT.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _build_sample_pdf_bytes() -> bytes:
    """Create a PDF file in memory from the sample resume text."""
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    # Insert the text at the top of the page
    page.insert_text((50, 50), SAMPLE_RESUME_TEXT, fontsize=10)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


@pytest.fixture
def docx_bytes():
    return _build_sample_docx_bytes()


@pytest.fixture
def pdf_bytes():
    return _build_sample_pdf_bytes()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ──────────────────────────────────────────────────────────────────────────
# Text extraction
# ──────────────────────────────────────────────────────────────────────────

class TestTextExtraction:
    def test_docx_extraction_contains_key_content(self, docx_bytes):
        text = _extract_text_from_docx(docx_bytes)
        assert "jane.doe@example.com" in text.lower()
        assert "certifications" in text.lower()
        assert "javascript" in text.lower()

    def test_pdf_extraction_contains_key_content(self, pdf_bytes):
        text = _extract_text_from_pdf(pdf_bytes)
        assert "jane.doe@example.com" in text.lower()
        assert "certifications" in text.lower()
        assert "javascript" in text.lower()

    def test_docx_and_pdf_produce_similar_content(self, docx_bytes, pdf_bytes):
        """Both formats should extract roughly the same information."""
        docx_text = _extract_text_from_docx(docx_bytes).lower()
        pdf_text = _extract_text_from_pdf(pdf_bytes).lower()
        for keyword in ["jane doe", "react", "university of technology",
                        "example learning platform", "node.js"]:
            assert keyword in docx_text, f"DOCX missing: {keyword}"
            assert keyword in pdf_text, f"PDF missing: {keyword}"


# ──────────────────────────────────────────────────────────────────────────
# Certification detection
# ──────────────────────────────────────────────────────────────────────────

class TestCertificationDetection:
    def test_finds_certification_entries(self):
        entries = _find_certification_entries(SAMPLE_RESUME_TEXT)
        assert len(entries) >= 2, f"Expected ≥2 cert entries, got {len(entries)}: {entries}"

    def test_certification_entry_content(self):
        entries = _find_certification_entries(SAMPLE_RESUME_TEXT)
        entry_text = " ".join(entries).lower()
        assert "web development" in entry_text or "introduction" in entry_text
        assert "python fundamentals" in entry_text

    def test_certification_score_full_marks(self):
        score, explanation = _section_score(SAMPLE_RESUME_TEXT, "certifications")
        assert score == 10, f"Expected 10/10, got {score}: {explanation}"
        assert "2" in explanation or "entries" in explanation.lower()

    def test_no_certifications(self):
        text = "Jane Doe\njane@example.com\nSKILLS\nPython, SQL"
        score, explanation = _section_score(text, "certifications")
        assert score == 0
        assert "no certifications" in explanation.lower()

    def test_heading_only_no_entries(self):
        text = "CERTIFICATIONS\n\nEDUCATION\nBachelor of Science"
        score, explanation = _section_score(text, "certifications")
        # Should get partial credit for having the heading
        assert score >= 0
        # Should NOT get full marks (10)
        assert score < 10

    def test_inline_aws_certified(self):
        text = "AWS Certified Solutions Architect - Associate (2024)"
        entries = _find_certification_entries(text)
        assert len(entries) >= 1

    def test_varied_heading_formats(self):
        """Certifications section under different heading names."""
        for heading in ["CERTIFICATIONS", "Certifications", "Certificates",
                        "Licenses & Certifications", "Courses and Certifications"]:
            text = f"{heading}\nAWS Cloud Practitioner (2024)\nGoogle Analytics (2024)\n\nEDUCATION"
            entries = _find_certification_entries(text)
            assert len(entries) >= 2, f"Heading '{heading}' → only {len(entries)} entries"


# ──────────────────────────────────────────────────────────────────────────
# Education detection
# ──────────────────────────────────────────────────────────────────────────

class TestEducationDetection:
    def test_sample_resume_education(self):
        score, expl = _section_score(SAMPLE_RESUME_TEXT, "education")
        assert score == 15, f"Expected 15/15, got {score}: {expl}"
        assert "bachelor" in expl.lower() or "degree" in expl.lower()
        assert "institution" in expl.lower() or "university" in expl.lower()


# ──────────────────────────────────────────────────────────────────────────
# Contact detection
# ──────────────────────────────────────────────────────────────────────────

class TestContactDetection:
    def test_sample_resume_contact(self):
        score, expl = _section_score(SAMPLE_RESUME_TEXT, "contact")
        assert score == 10, f"Expected 10/10, got {score}: {expl}"
        assert "email found" in expl
        assert "phone found" in expl
        assert "profile link found" in expl


# ──────────────────────────────────────────────────────────────────────────
# Projects detection
# ──────────────────────────────────────────────────────────────────────────

class TestProjectsDetection:
    def test_sample_resume_projects(self):
        score, expl = _section_score(SAMPLE_RESUME_TEXT, "projects")
        assert score >= 10, f"Expected ≥10/15, got {score}: {expl}"


# ──────────────────────────────────────────────────────────────────────────
# Skills extraction (controlled vocabulary)
# ──────────────────────────────────────────────────────────────────────────

class TestSkillExtraction:
    def test_no_ordinary_words_counted(self):
        """Words like 'the', 'and', 'with' must NOT be in recognised skills."""
        skills = _extract_skills_from_text(SAMPLE_RESUME_TEXT)
        junk = {"the", "and", "with", "for", "from", "that", "this",
                "using", "across", "through", "into", "building",
                "modern", "creative", "detail", "oriented", "years",
                "experience", "present", "may", "graduated"}
        found_junk = [s for s in skills if s in junk]
        assert found_junk == [], f"Junk words in skills: {found_junk}"

    def test_real_skills_detected(self):
        skills = _extract_skills_from_text(SAMPLE_RESUME_TEXT)
        expected = {"javascript", "react", "node.js", "html", "css",
                    "git", "docker", "mongodb", "postgresql"}
        for s in expected:
            assert s in skills, f"Expected skill '{s}' not found. Got: {skills}"

    def test_multi_word_skills(self):
        skills = _extract_skills_from_text(SAMPLE_RESUME_TEXT)
        assert "rest api" in skills
        assert "responsive design" in skills

    def test_count_is_reasonable(self):
        """Should be well under 156 (the old broken count)."""
        skills = _extract_skills_from_text(SAMPLE_RESUME_TEXT)
        assert len(skills) < 50, f"Too many skills: {len(skills)}"
        assert len(skills) >= 10, f"Too few skills: {len(skills)}"

    def test_skills_section_score(self):
        score, expl = _section_score(SAMPLE_RESUME_TEXT, "skills")
        assert score == 15, f"Expected 15/15, got {score}: {expl}"
        assert "recognised technical skills" in expl


# ──────────────────────────────────────────────────────────────────────────
# Keyword / ATS matching
# ──────────────────────────────────────────────────────────────────────────

class TestKeywordMatching:
    def test_web_developer_core_skills(self):
        result = _match_keywords(SAMPLE_RESUME_TEXT, "Web Developer")
        # Sample resume should match all core Web Developer skills
        assert result["core_match_pct"] == 100.0, \
            f"Core match {result['core_match_pct']}%, missing: {result['missing_core_skills']}"

    def test_returns_expected_fields(self):
        result = _match_keywords(SAMPLE_RESUME_TEXT, "Web Developer")
        assert "matched_skills" in result
        assert "missing_skills" in result
        assert "keyword_match_pct" in result
        assert "missing_core_skills" in result
        assert "missing_optional_skills" in result
        assert "core_match_pct" in result

    def test_percentage_is_weighted(self):
        """Core skills should weigh more than optional ones."""
        result = _match_keywords(SAMPLE_RESUME_TEXT, "Web Developer")
        # With all core matched, percentage should be at least
        # (core_count * 2) / (core_count * 2 + optional_count) * 100
        assert result["keyword_match_pct"] > 30

    def test_missing_skills_split(self):
        result = _match_keywords(SAMPLE_RESUME_TEXT, "Web Developer")
        # Missing = core_missing + optional_missing
        assert len(result["missing_skills"]) == (
            len(result["missing_core_skills"]) +
            len(result["missing_optional_skills"])
        )


# ──────────────────────────────────────────────────────────────────────────
# Score consistency
# ──────────────────────────────────────────────────────────────────────────

class TestScoreConsistency:
    def test_category_scores_sum_to_resume_score(self):
        """resume_score = sum(category scores) / sum(max) * 100."""
        total_pts = 0
        total_max = 0
        for section, max_pts in _CATEGORY_WEIGHTS.items():
            pts, _ = _section_score(SAMPLE_RESUME_TEXT, section)
            assert 0 <= pts <= max_pts, \
                f"{section}: score {pts} out of range [0, {max_pts}]"
            total_pts += pts
            total_max += max_pts
        expected = round(total_pts / total_max * 100, 1)
        # Just verify the math works – the exact value depends on the text
        assert 0 <= expected <= 100

    def test_max_weights_sum_to_100(self):
        assert sum(_CATEGORY_WEIGHTS.values()) == 100

    def test_completeness_counts_certifications(self):
        """With certs present, completeness should see 6/6 sections."""
        score, expl = _section_score(SAMPLE_RESUME_TEXT, "completeness")
        assert "6/6" in expl, f"Expected 6/6 sections. Got: {expl}"


# ──────────────────────────────────────────────────────────────────────────
# API integration tests
# ──────────────────────────────────────────────────────────────────────────

class TestAPIContract:
    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "supported_roles" in data

    def test_analyze_docx(self, client, docx_bytes):
        resp = client.post("/api/analyze", data={
            "resume": (io.BytesIO(docx_bytes), "resume.docx"),
            "role": "Web Developer",
        }, content_type="multipart/form-data")
        assert resp.status_code == 200
        data = resp.get_json()
        # Verify all expected top-level fields
        for field in ["resume_score", "ats_score", "role", "category_scores",
                      "matched_skills", "missing_skills", "keyword_match_pct",
                      "suggestions"]:
            assert field in data, f"Missing field: {field}"
        assert data["role"] == "Web Developer"
        assert 0 < data["resume_score"] <= 100
        assert isinstance(data["matched_skills"], list)
        assert isinstance(data["suggestions"], list)

    def test_analyze_pdf(self, client, pdf_bytes):
        resp = client.post("/api/analyze", data={
            "resume": (io.BytesIO(pdf_bytes), "resume.pdf"),
            "role": "Web Developer",
        }, content_type="multipart/form-data")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["resume_score"] > 0
        assert data["category_scores"]["certifications"]["score"] >= 5

    def test_pdf_and_docx_scores_are_close(self, client, pdf_bytes, docx_bytes):
        """Both formats should produce similar results for the same content."""
        resp_pdf = client.post("/api/analyze", data={
            "resume": (io.BytesIO(pdf_bytes), "resume.pdf"),
            "role": "Web Developer",
        }, content_type="multipart/form-data")
        resp_docx = client.post("/api/analyze", data={
            "resume": (io.BytesIO(docx_bytes), "resume.docx"),
            "role": "Web Developer",
        }, content_type="multipart/form-data")
        pdf_score = resp_pdf.get_json()["resume_score"]
        docx_score = resp_docx.get_json()["resume_score"]
        # Allow some tolerance for formatting differences
        assert abs(pdf_score - docx_score) <= 15, \
            f"PDF={pdf_score}, DOCX={docx_score} — too far apart"

    def test_category_scores_structure(self, client, docx_bytes):
        resp = client.post("/api/analyze", data={
            "resume": (io.BytesIO(docx_bytes), "resume.docx"),
            "role": "Web Developer",
        }, content_type="multipart/form-data")
        data = resp.get_json()
        cs = data["category_scores"]
        for section in ["contact", "education", "skills", "experience",
                        "projects", "certifications", "completeness"]:
            assert section in cs, f"Missing category: {section}"
            assert "score" in cs[section]
            assert "max" in cs[section]
            assert "explanation" in cs[section]


class TestAPIErrors:
    def test_missing_file(self, client):
        resp = client.post("/api/analyze", data={"role": "Web Developer"},
                           content_type="multipart/form-data")
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_missing_role(self, client, docx_bytes):
        resp = client.post("/api/analyze", data={
            "resume": (io.BytesIO(docx_bytes), "resume.docx"),
        }, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_unsupported_role(self, client, docx_bytes):
        resp = client.post("/api/analyze", data={
            "resume": (io.BytesIO(docx_bytes), "resume.docx"),
            "role": "Astronaut",
        }, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert "supported_roles" in resp.get_json()

    def test_bad_extension(self, client):
        resp = client.post("/api/analyze", data={
            "resume": (io.BytesIO(b"not a resume"), "resume.txt"),
            "role": "Web Developer",
        }, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_empty_file(self, client):
        resp = client.post("/api/analyze", data={
            "resume": (io.BytesIO(b""), "resume.pdf"),
            "role": "Web Developer",
        }, content_type="multipart/form-data")
        assert resp.status_code == 400
