from flask import Flask, render_template, request
from pypdf import PdfReader
import pytesseract
import fitz
import re

import os

if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "tesseract"
app = Flask(__name__)


def extract_resume_text(pdf_file):
    # First try normal PDF text extraction
    reader = PdfReader(pdf_file)
    resume_text = ""

    for page in reader.pages:
        resume_text += page.extract_text() or ""

    # If normal extraction works, use it
    if resume_text.strip():
        return resume_text

    # Otherwise use OCR
    pdf_file.seek(0)

    pdf_bytes = pdf_file.read()
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

    ocr_text = ""

    for page in pdf_document:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image = pix.tobytes("png")

        from PIL import Image
        from io import BytesIO

        pil_image = Image.open(BytesIO(image))

        text = pytesseract.image_to_string(pil_image)
        ocr_text += text + "\n"

    pdf_document.close()

    return ocr_text


def contains_skill(text, skill):
    text = text.lower()
    skill = skill.lower()

    # Special handling for skills containing symbols
    if skill in ["c", "c++", "node.js"]:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill) + r"(?![a-zA-Z0-9])"
    else:
        pattern = r"\b" + re.escape(skill) + r"\b"

    return re.search(pattern, text) is not None


@app.route("/", methods=["GET", "POST"])
def home():

    result = None
    error = None

    if request.method == "POST":

        resume = request.files.get("resume")
        job_description = request.form.get("job_description", "").strip()

        # Check whether a file was uploaded
        if not resume or resume.filename == "":
            error = "Please upload a resume PDF."

            return render_template(
                "index.html",
                result=result,
                error=error
            )

        # Check file type
        if not resume.filename.lower().endswith(".pdf"):
            error = "Only PDF resume files are supported."

            return render_template(
                "index.html",
                result=result,
                error=error
            )

        # Check job description
        if not job_description:
            error = "Please enter a job description."

            return render_template(
                "index.html",
                result=result,
                error=error
            )

        # Extract resume text
        resume_text = extract_resume_text(resume)

        print("EXTRACTED RESUME TEXT:")
        print(resume_text)

        skills = [
            "python",
            "java",
            "javascript",
            "typescript",
            "c",
            "c++",
            "html",
            "css",
            "sql",
            "mysql",
            "mongodb",
            "flask",
            "django",
            "react",
            "node.js",
            "git",
            "github",
            "aws",
            "docker",
            "excel",
            "power bi",
            "machine learning",
            "data analysis"
        ]

        # Find required skills in job description
        required_skills = [
            skill
            for skill in skills
            if contains_skill(job_description, skill)
        ]

        # Check whether recognizable skills exist
        if not required_skills:
            error = (
                "No recognized technical skills were found "
                "in the job description."
            )

            return render_template(
                "index.html",
                result=result,
                error=error
            )

        # Find skills from the job description that are present in resume
        matched_skills = [
            skill
            for skill in required_skills
            if contains_skill(resume_text, skill)
        ]

        # Find required skills missing from resume
        missing_skills = [
            skill
            for skill in required_skills
            if not contains_skill(resume_text, skill)
        ]

        # Calculate match percentage
        match_score = round(
            len(matched_skills)
            / len(required_skills)
            * 100
        )

        # Recommend missing skills
        recommended_skills = missing_skills

        # Store screening result
        result = {
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "recommended_skills": recommended_skills,
            "matched_count": len(matched_skills),
            "required_count": len(required_skills)
        }

    return render_template(
        "index.html",
        result=result,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)