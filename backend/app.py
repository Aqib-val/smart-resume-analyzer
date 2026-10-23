"""
Smart Resume Analyzer – Flask Backend
======================================
Analyzes uploaded resumes (PDF / DOCX) against a chosen job role and returns
a transparent score breakdown, ATS keyword-match results, and actionable
improvement suggestions.

Endpoints
---------
GET  /api/health   – liveness probe
POST /api/analyze  – upload a resume + role, get analysis JSON
"""

import os
import re
import io

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# PDF extraction
import pymupdf

# DOCX extraction
from docx import Document

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

# In production, serve the Vite-built frontend from ../frontend/dist
_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

app = Flask(
    __name__,
    static_folder=os.path.abspath(_FRONTEND_DIST),
    static_url_path="",
)
CORS(app)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {"pdf", "docx"}

# ---------------------------------------------------------------------------
# Controlled vocabulary of known technical skills / technologies
# ---------------------------------------------------------------------------
# Used for the "skills" category scoring (section richness) instead of
# counting every word.  Kept lowercase for case-insensitive matching.
KNOWN_SKILLS: set[str] = {
    # Languages
    "python", "javascript", "typescript", "java", "c", "c++", "c#", "go",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
    "perl", "lua", "dart", "elixir", "haskell", "sql", "nosql", "bash",
    "shell", "powershell",
    # Web frontend
    "html", "css", "sass", "less", "tailwind", "bootstrap", "react",
    "angular", "vue", "svelte", "next.js", "nuxt.js", "gatsby",
    "webpack", "vite", "rollup", "parcel", "babel",
    # Web backend & frameworks
    "node.js", "express", "django", "flask", "fastapi", "spring",
    "spring boot", "rails", "laravel", "asp.net", "gin", "fiber",
    # Databases
    "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
    "cassandra", "dynamodb", "couchdb", "neo4j", "elasticsearch",
    "firebase", "supabase", "bigquery", "snowflake",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "github actions", "gitlab ci", "ci/cd",
    "cloudformation", "helm", "prometheus", "grafana", "datadog",
    "nginx", "apache", "linux", "serverless", "microservices",
    # Data & ML
    "pandas", "numpy", "matplotlib", "seaborn", "scikit-learn",
    "tensorflow", "pytorch", "keras", "opencv", "nltk", "spacy",
    "hugging face", "langchain", "openai", "mlflow", "airflow",
    "spark", "hadoop", "kafka", "dbt", "tableau", "power bi",
    "looker", "jupyter", "machine learning", "deep learning",
    "nlp", "computer vision", "reinforcement learning",
    "neural networks", "transformers", "llm", "rag",
    "data visualization", "data modeling", "etl",
    "feature engineering", "data preprocessing", "mlops",
    # APIs & protocols
    "rest api", "graphql", "grpc", "websocket", "oauth",
    # Testing
    "jest", "mocha", "pytest", "junit", "selenium", "cypress",
    "playwright",
    # Tools
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "figma", "postman", "swagger",
    # Concepts
    "responsive design", "accessibility", "agile", "scrum",
    "devops", "load balancing", "networking",
    # Cloud specific
    "s3", "ec2", "lambda", "vpc", "iam", "cloud functions",
    "sagemaker", "vertex ai",
    # Other
    "excel", "google analytics", "a/b testing",
    "hypothesis testing", "regression", "statistics",
    "data cleaning", "data wrangling", "dashboards", "kpi",
    "model deployment", "vector databases",
}

# Pre-sort by length descending so multi-word skills are matched first
_KNOWN_SKILLS_SORTED: list[str] = sorted(KNOWN_SKILLS, key=len, reverse=True)

# ---------------------------------------------------------------------------
# Role-specific keyword banks – separated into core and optional
# ---------------------------------------------------------------------------
# core:     Fundamental skills an applicant should have.
# optional: Useful but not required; missing them is not a red flag.
ROLE_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "Data Analyst": {
        "core": [
            "sql", "python", "excel", "data visualization",
            "statistics", "data cleaning", "dashboards",
        ],
        "optional": [
            "r", "tableau", "power bi", "pandas", "numpy",
            "matplotlib", "seaborn", "data wrangling", "etl",
            "bigquery", "looker", "jupyter", "hypothesis testing",
            "regression", "a/b testing", "google analytics", "kpi",
            "data modeling",
        ],
    },
    "Web Developer": {
        "core": [
            "html", "css", "javascript", "git",
            "responsive design", "rest api",
        ],
        "optional": [
            "typescript", "react", "angular", "vue", "node.js",
            "express", "next.js", "tailwind", "bootstrap", "sass",
            "webpack", "graphql", "mongodb", "postgresql", "mysql",
            "firebase", "docker", "ci/cd", "jest", "figma",
            "accessibility",
        ],
    },
    "AI Engineer": {
        "core": [
            "python", "machine learning", "deep learning",
            "data preprocessing", "neural networks",
        ],
        "optional": [
            "tensorflow", "pytorch", "keras", "scikit-learn", "nlp",
            "computer vision", "transformers", "hugging face",
            "langchain", "llm", "openai", "gpt", "bert",
            "reinforcement learning", "feature engineering", "mlops",
            "docker", "kubernetes", "sagemaker", "vertex ai",
            "model deployment", "rag", "vector databases",
        ],
    },
    "Cloud Engineer": {
        "core": [
            "linux", "docker", "networking", "ci/cd", "git",
            "iam",
        ],
        "optional": [
            "aws", "azure", "gcp", "terraform", "cloudformation",
            "kubernetes", "jenkins", "vpc", "s3", "ec2", "lambda",
            "cloud functions", "load balancing", "monitoring",
            "prometheus", "grafana", "ansible", "helm",
            "microservices", "serverless", "devops", "bash",
        ],
    },
}

SUPPORTED_ROLES = list(ROLE_KEYWORDS.keys())

# Flat keyword lists for backward-compat helpers
def _all_keywords(role: str) -> list[str]:
    """Return combined core + optional keywords for a role."""
    rd = ROLE_KEYWORDS[role]
    return rd["core"] + rd["optional"]

# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------

def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF stored in memory."""
    text_parts: list[str] = []
    with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from a DOCX stored in memory."""
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs)

# ---------------------------------------------------------------------------
# Resume section detection
# ---------------------------------------------------------------------------

# Patterns used to locate common resume sections.
# The certifications pattern now also matches common certification-entry
# keywords (course, completion, certificate name patterns) so that
# individual cert entries are counted, not just the section heading.
_SECTION_PATTERNS: dict[str, re.Pattern] = {
    "contact":        re.compile(
        r"([\w.+-]+@[\w-]+\.[\w.]+)|(\+?\d[\d\s\-()]{7,}\d)|(linkedin\.com|github\.com)",
        re.IGNORECASE,
    ),
    "education":      re.compile(
        r"\b(bachelor|master|b\.?sc|m\.?sc|b\.?tech|m\.?tech|b\.?e|m\.?e|"
        r"ph\.?d|diploma|degree|university|college|institute|gpa|cgpa|"
        r"computer science|information technology|engineering|mba|bca|mca)\b",
        re.IGNORECASE,
    ),
    "skills":         re.compile(
        r"\b(skills?|technical skills?|technologies|proficien|competenc|tools?)\b",
        re.IGNORECASE,
    ),
    "experience":     re.compile(
        r"\b(experience|work history|employment|intern|worked at|company|"
        r"responsibilities|duties|role|position|job title)\b",
        re.IGNORECASE,
    ),
    "projects":       re.compile(
        r"\b(projects?|portfolio|case study|developed|built|created|"
        r"implemented|designed|architected)\b",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"\b(certific\w*|licensed|accredit\w*|credential\w*|"
        r"aws certified|google certified|azure certified|"
        r"professional certificate)\b",
        re.IGNORECASE,
    ),
}


def _extract_skills_from_text(text: str) -> list[str]:
    """
    Extract recognised technical skills from resume text using the
    controlled vocabulary.  Returns a sorted, de-duplicated list.

    Multi-word skills are matched first (longest-match-first) so that
    e.g. "machine learning" is not split into separate words.
    """
    text_lower = text.lower()
    found: set[str] = set()

    for skill in _KNOWN_SKILLS_SORTED:
        # Use word-boundary matching for single-word skills.
        # For multi-word / special-char skills, use plain substring match.
        if " " in skill or "." in skill or "/" in skill or "+" in skill or "#" in skill:
            if skill in text_lower:
                found.add(skill)
        else:
            if re.search(rf"\b{re.escape(skill)}\b", text_lower):
                found.add(skill)

    return sorted(found)


def _find_certification_entries(text: str) -> list[str]:
    """
    Detect individual certification / course entries in a resume.

    Strategy:
    1. Look for a certifications section by heading.
    2. If found, count non-empty lines under it as entries.
    3. Also count standalone certification keywords anywhere
       (e.g. "AWS Certified", "certificate", "certified").

    Returns a list of matched entry descriptions (may contain
    duplicates removed by caller if needed).
    """
    lines = text.split("\n")
    entries: list[str] = []

    # ── Strategy 1: locate a section heading and gather entries below it ──
    # Headings: "CERTIFICATIONS", "Certifications", "Certificates",
    #           "LICENSES & CERTIFICATIONS", "Courses & Certifications", etc.
    heading_re = re.compile(
        r"^\s*(certific\w*|licen[sc]es?\s*(?:[&/,]|and)\s*certific\w*|"
        r"courses?\s*(?:[&/,]|and)\s*certific\w*|"
        r"professional\s+development|"
        r"training\s*(?:[&/,]|and)\s*certific\w*)\s*:?\s*$",
        re.IGNORECASE,
    )
    # Next-section heading (any ALL-CAPS line ≥3 chars or title-case heading)
    next_heading_re = re.compile(
        r"^\s*[A-Z][A-Z\s&/,]{2,}\s*$|"
        r"^\s*(?:Education|Experience|Skills|Projects|Summary|Objective|"
        r"Contact|References|Languages|Hobbies|Interests|Awards)\s*:?\s*$",
        re.IGNORECASE,
    )

    in_cert_section = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if heading_re.match(stripped):
            in_cert_section = True
            continue

        if in_cert_section:
            # Stop at next section heading
            if next_heading_re.match(stripped) and not heading_re.match(stripped):
                in_cert_section = False
                continue
            # Count this as a cert entry if it has meaningful content
            # (skip very short lines that are just bullets or dashes)
            cleaned = re.sub(r"^[\-•·▪◦→*]\s*", "", stripped)
            if len(cleaned) >= 5:
                entries.append(cleaned)

    # ── Strategy 2: keyword-based detection for inline certs ──
    # Catch patterns like "Certified Kubernetes Administrator" or
    # "AWS Certified Solutions Architect" even if not in a section.
    inline_re = re.compile(
        r"(?:aws|google|azure|microsoft|oracle|cisco|comptia|pmp|"
        r"scrum|itil|prince2)[\s\-]+certified\b|"
        r"\bcertified\s+(?:developer|architect|engineer|associate|"
        r"professional|practitioner|administrator|specialist)\b|"
        r"\bcertificate\s+(?:in|of)\b",
        re.IGNORECASE,
    )
    for m in inline_re.finditer(text):
        entries.append(m.group(0).strip())

    return entries


def _section_score(text: str, section: str) -> tuple[int, str]:
    """
    Return (score_out_of_max, explanation) for a single resume section.

    Scoring rubric (out of each section's weight):
      - contact info  (10):  email +4, phone +3, profile link +3
      - education     (15):  degree mention +8, institution +7
      - skills        (15):  header +5, ≥5 skills +5, ≥10 +5
      - experience    (20):  header +5, ≥1 role +5, ≥2 roles +5, quantified +5
      - projects      (15):  header +5, ≥1 project +5, ≥2 +5
      - certifications(10):  any entry +5, ≥2 entries +5
      - completeness  (15):  length, formatting, and section diversity
    """
    text_lower = text.lower()

    if section == "contact":
        score = 0
        details = []
        if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text):
            score += 4; details.append("email found")
        else:
            details.append("no email detected")
        if re.search(r"\+?\d[\d\s\-()]{7,}\d", text):
            score += 3; details.append("phone found")
        else:
            details.append("no phone number detected")
        if re.search(r"(linkedin\.com|github\.com)", text_lower):
            score += 3; details.append("profile link found")
        else:
            details.append("no LinkedIn/GitHub link detected")
        return score, "; ".join(details)

    if section == "education":
        score = 0
        details = []
        degree_kw = re.findall(
            r"\b(bachelor|master|b\.?sc|m\.?sc|b\.?tech|m\.?tech|b\.?e|m\.?e|"
            r"ph\.?d|diploma|degree|mba|bca|mca)\b",
            text_lower,
        )
        if degree_kw:
            score += 8; details.append(f"degree keyword(s): {', '.join(set(degree_kw[:3]))}")
        else:
            details.append("no degree/qualification keyword found")
        if re.search(r"\b(university|college|institute)\b", text_lower):
            score += 7; details.append("institution mentioned")
        else:
            details.append("no institution name detected")
        return score, "; ".join(details)

    if section == "skills":
        score = 0
        details = []
        if _SECTION_PATTERNS["skills"].search(text):
            score += 5; details.append("skills section header present")
        else:
            details.append("no explicit skills section header")
        # Use controlled vocabulary instead of arbitrary token counting
        recognized = _extract_skills_from_text(text)
        n = len(recognized)
        if n >= 10:
            score += 10; details.append(f"{n} recognised technical skills (≥10)")
        elif n >= 5:
            score += 5; details.append(f"{n} recognised technical skills (≥5)")
        else:
            details.append(f"only {n} recognised technical skills found")
        return score, "; ".join(details)

    if section == "experience":
        score = 0
        details = []
        if _SECTION_PATTERNS["experience"].search(text):
            score += 5; details.append("experience section detected")
        else:
            details.append("no clear experience section detected")
        roles = re.findall(
            r"\b(intern|engineer|developer|analyst|manager|lead|architect|"
            r"consultant|specialist|designer|coordinator|associate)\b",
            text_lower,
        )
        unique_roles = set(roles)
        if len(unique_roles) >= 2:
            score += 10; details.append(f"multiple role titles ({', '.join(list(unique_roles)[:3])})")
        elif len(unique_roles) == 1:
            score += 5; details.append(f"role title: {unique_roles.pop()}")
        else:
            details.append("no role/title keywords found")
        # Quantified achievements
        quant = re.findall(r"\d+\s*[%+]|\d{2,}[+]?\s*(users?|clients?|projects?|reduction|increase)", text_lower)
        if quant:
            score += 5; details.append("quantified achievements found")
        else:
            details.append("no quantified achievements – add metrics!")
        return score, "; ".join(details)

    if section == "projects":
        score = 0
        details = []
        if _SECTION_PATTERNS["projects"].search(text):
            score += 5; details.append("projects section detected")
        else:
            details.append("no projects section detected")
        project_verbs = re.findall(
            r"\b(developed|built|created|implemented|designed|architected|"
            r"deployed|automated|integrated|launched)\b",
            text_lower,
        )
        n = len(set(project_verbs))
        if n >= 2:
            score += 10; details.append(f"strong project verbs: {', '.join(set(project_verbs))}")
        elif n == 1:
            score += 5; details.append(f"project verb: {project_verbs[0]}")
        else:
            details.append("no project-related action verbs found")
        return score, "; ".join(details)

    if section == "certifications":
        score = 0
        details = []
        # Use the improved entry-level detection
        cert_entries = _find_certification_entries(text)
        # Also check if the section heading itself is present
        has_heading = bool(re.search(
            r"\b(certific\w*|licen[sc]es?\s*(?:[&/,]|and)\s*certific\w*)\b",
            text, re.IGNORECASE,
        ))
        n = len(cert_entries)
        if n >= 2:
            score += 10; details.append(f"{n} certification entries detected")
        elif n == 1:
            score += 5; details.append("1 certification entry detected")
        elif has_heading:
            # Heading present but no parseable entries
            score += 3; details.append("certification section heading found but no entries parsed")
        else:
            details.append("no certifications detected")
        return score, "; ".join(details)

    # completeness (catch-all quality signals)
    if section == "completeness":
        score = 0
        details = []
        word_count = len(text.split())
        if word_count >= 300:
            score += 5; details.append(f"good length ({word_count} words)")
        elif word_count >= 150:
            score += 3; details.append(f"moderate length ({word_count} words)")
        else:
            details.append(f"too short ({word_count} words) – add more detail")
        # Section diversity – use both pattern detection AND heading-based
        # detection for certifications so it isn't missed
        sections_found = 0
        for key, pat in _SECTION_PATTERNS.items():
            if key == "certifications":
                # For certifications, also check heading presence
                if pat.search(text) or _find_certification_entries(text):
                    sections_found += 1
            else:
                if pat.search(text):
                    sections_found += 1
        if sections_found >= 5:
            score += 5; details.append(f"{sections_found}/6 key sections present")
        elif sections_found >= 3:
            score += 3; details.append(f"only {sections_found}/6 key sections present")
        else:
            details.append(f"only {sections_found}/6 key sections – very incomplete")
        # Bullet / action-verb density
        action_verbs = len(re.findall(
            r"\b(managed|led|developed|designed|improved|increased|reduced|"
            r"achieved|delivered|optimized|analyzed|coordinated|spearheaded)\b",
            text_lower,
        ))
        if action_verbs >= 5:
            score += 5; details.append("strong use of action verbs")
        elif action_verbs >= 2:
            score += 3; details.append("some action verbs – use more")
        else:
            details.append("weak action-verb usage – strengthen bullet points")
        return score, "; ".join(details)

    return 0, "unknown section"

# Maximum possible points per category
_CATEGORY_WEIGHTS = {
    "contact":        10,
    "education":      15,
    "skills":         15,
    "experience":     20,
    "projects":       15,
    "certifications": 10,
    "completeness":   15,
}

# ---------------------------------------------------------------------------
# Keyword / ATS matching
# ---------------------------------------------------------------------------

def _match_keywords(text: str, role: str) -> dict:
    """
    Compare resume text against role-specific keywords.

    Returns matched / missing for both core and optional skill lists,
    plus a weighted match percentage (core skills count more).
    """
    rd = ROLE_KEYWORDS[role]
    core = rd["core"]
    optional = rd["optional"]
    text_lower = text.lower()

    core_matched = [kw for kw in core if kw in text_lower]
    core_missing = [kw for kw in core if kw not in text_lower]
    opt_matched  = [kw for kw in optional if kw in text_lower]
    opt_missing  = [kw for kw in optional if kw not in text_lower]

    all_matched = sorted(core_matched + opt_matched)
    all_missing_core = sorted(core_missing)
    all_missing_optional = sorted(opt_missing)

    # Weighted percentage: core skills are worth 2× each
    total_weight = len(core) * 2 + len(optional)
    matched_weight = len(core_matched) * 2 + len(opt_matched)
    pct = round(matched_weight / total_weight * 100, 1) if total_weight else 0

    return {
        "matched_skills": all_matched,
        "missing_skills": all_missing_core + all_missing_optional,
        "missing_core_skills": all_missing_core,
        "missing_optional_skills": all_missing_optional,
        "keyword_match_pct": pct,
        "core_match_pct": round(
            len(core_matched) / len(core) * 100, 1
        ) if core else 0,
    }

# ---------------------------------------------------------------------------
# Suggestion generator
# ---------------------------------------------------------------------------

def _generate_suggestions(
    category_scores: dict,
    keyword_result: dict,
    role: str,
) -> list[str]:
    """Produce actionable, context-specific improvement tips."""
    tips: list[str] = []

    # Category-driven suggestions
    cs = category_scores
    if cs["contact"]["score"] < cs["contact"]["max"]:
        missing_parts = []
        expl = cs["contact"]["explanation"].lower()
        if "no email" in expl:
            missing_parts.append("a professional email address")
        if "no phone" in expl:
            missing_parts.append("a phone number")
        if "no linkedin" in expl or "no link" in expl:
            missing_parts.append("a LinkedIn or GitHub profile link")
        if missing_parts:
            tips.append(f"Add {', '.join(missing_parts)} to your contact section.")

    if cs["education"]["score"] < cs["education"]["max"]:
        tips.append(
            "Strengthen your education section – include your degree name, "
            "field of study, institution, and graduation year."
        )

    if cs["skills"]["score"] < cs["skills"]["max"]:
        tips.append(
            "Create a dedicated 'Skills' or 'Technical Skills' section and list "
            "at least 10 relevant technologies or competencies."
        )

    if cs["experience"]["score"] < cs["experience"]["max"]:
        expl = cs["experience"]["explanation"].lower()
        if "no quantified" in expl:
            tips.append(
                "Quantify your achievements – e.g., 'Reduced load time by 40%' "
                "or 'Managed a team of 5 engineers.'"
            )
        if "no role" in expl or "no clear" in expl:
            tips.append(
                "Clearly state your job titles, companies, and date ranges in "
                "a dedicated Experience section."
            )

    if cs["projects"]["score"] < cs["projects"]["max"]:
        tips.append(
            "Add a Projects section highlighting 2-3 relevant projects with "
            "the tech stack used and measurable outcomes."
        )

    if cs["certifications"]["score"] < cs["certifications"]["max"]:
        tips.append(
            f"Consider earning certifications relevant to {role} and listing "
            "them on your resume to boost credibility."
        )

    if cs["completeness"]["score"] < cs["completeness"]["max"]:
        expl = cs["completeness"]["explanation"].lower()
        if "too short" in expl:
            tips.append(
                "Your resume is quite short. Expand descriptions of your roles, "
                "projects, and skills."
            )
        if "action" in expl and "weak" in expl:
            tips.append(
                "Use strong action verbs to start bullet points – e.g., "
                "'Developed', 'Led', 'Optimized', 'Designed'."
            )

    # ATS-driven suggestions – differentiate core from optional
    missing_core = keyword_result.get("missing_core_skills", [])
    missing_opt = keyword_result.get("missing_optional_skills", [])
    pct = keyword_result["keyword_match_pct"]

    if missing_core:
        sample = ", ".join(missing_core[:5])
        tips.append(
            f"You're missing core {role} skills: {sample}. "
            "These are fundamental – add them if you have the experience."
        )
    if pct < 50 and missing_opt:
        sample = ", ".join(missing_opt[:4])
        tips.append(
            f"Your overall keyword match for {role} is {pct}%. "
            f"Consider adding optional skills like: {sample}."
        )
    elif missing_opt and not missing_core:
        sample = ", ".join(missing_opt[:4])
        tips.append(
            f"To further improve ATS compatibility, consider adding: {sample}."
        )

    if not tips:
        tips.append("Great job! Your resume looks well-structured for this role.")

    return tips

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    """Liveness check."""
    return jsonify({
        "status": "ok",
        "message": "Smart Resume Analyzer API is running.",
        "supported_roles": SUPPORTED_ROLES,
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Accept a resume file + role, return structured analysis JSON."""

    # ---- Validate role ----
    role = request.form.get("role", "").strip()
    if not role:
        return jsonify({"error": "Missing required field: 'role'."}), 400
    if role not in ROLE_KEYWORDS:
        return jsonify({
            "error": f"Unsupported role: '{role}'.",
            "supported_roles": SUPPORTED_ROLES,
        }), 400

    # ---- Validate file ----
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded. Send a file under the 'resume' field."}), 400

    file = request.files["resume"]
    if file.filename == "" or file.filename is None:
        return jsonify({"error": "Uploaded file has no filename."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "error": f"Unsupported file type: '.{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}.",
        }), 400

    file_bytes = file.read()

    if len(file_bytes) == 0:
        return jsonify({"error": "Uploaded file is empty."}), 400
    if len(file_bytes) > MAX_FILE_SIZE:
        return jsonify({
            "error": f"File exceeds the 5 MB limit ({len(file_bytes) / (1024*1024):.1f} MB).",
        }), 413

    # ---- Extract text ----
    try:
        if ext == "pdf":
            text = _extract_text_from_pdf(file_bytes)
        else:
            text = _extract_text_from_docx(file_bytes)
    except Exception:
        return jsonify({"error": "Could not read the file. It may be corrupted or password-protected."}), 422

    text = text.strip()
    if not text:
        return jsonify({"error": "No readable text found in the uploaded file."}), 422

    # ---- Score each category ----
    category_scores: dict[str, dict] = {}
    total_score = 0
    total_max = 0
    for section, max_pts in _CATEGORY_WEIGHTS.items():
        pts, explanation = _section_score(text, section)
        category_scores[section] = {
            "score": pts,
            "max": max_pts,
            "explanation": explanation,
        }
        total_score += pts
        total_max += max_pts

    resume_score = round(total_score / total_max * 100, 1) if total_max else 0

    # ---- Keyword / ATS matching ----
    keyword_result = _match_keywords(text, role)
    ats_score = keyword_result["keyword_match_pct"]

    # ---- Suggestions ----
    suggestions = _generate_suggestions(category_scores, keyword_result, role)

    # ---- Build response (never log or persist the resume text) ----
    return jsonify({
        "resume_score": resume_score,
        "ats_score": ats_score,
        "role": role,
        "category_scores": category_scores,
        "matched_skills": keyword_result["matched_skills"],
        "missing_skills": keyword_result["missing_skills"],
        "keyword_match_pct": keyword_result["keyword_match_pct"],
        "suggestions": suggestions,
    })


# ---------------------------------------------------------------------------
# Serve React frontend (production)
# ---------------------------------------------------------------------------

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve the Vite-built React app for any non-API route."""
    # If the requested file exists in dist/, serve it directly
    full_path = os.path.join(app.static_folder, path)
    if path and os.path.isfile(full_path):
        return send_from_directory(app.static_folder, path)
    # Otherwise serve index.html (client-side routing)
    return send_from_directory(app.static_folder, "index.html")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
