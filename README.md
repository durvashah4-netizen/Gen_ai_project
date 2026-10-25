# Sitewise: Multimodal Construction Intelligence

A Streamlit decision-support prototype for construction site photo review, crack observations, first-pass planning estimates, and weather-aware site guidance. It runs without a database and supports a no-key demonstration mode.

## Start locally

Python 3.9 or newer is required.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Without a key, image modules and chat use clearly labeled demonstration responses. Add a Groq API key in the password field in the sidebar, or set `GROQ_API_KEY` in the environment before starting the app. The app does not write the key or uploaded files to disk. Set `GROQ_MODEL` to select a different vision-capable model available to your Groq account.

## Modules

- Site safety audit: visual PPE checklist, site hazards, JSON download. Model-backed image analysis requires a vision-capable Groq model.
- Crack diagnostics: visible defect summary, approximate width, possible causes, review options, JSON download.
- Planning and valuation: indicative budget, capex, material allowances, milestone progress, and a Pollinations concept-render link.
- Daily site assistant: weather protocols and a multi-turn construction Q&A.

## Verify

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py construction_platform.py domain.py
```

## Important limitations

AI image observations are not inspections, certifications, engineering assessments, or code-compliance decisions. Image-based PPE classification and crack measurements can be wrong or incomplete. Budget, valuation, and material figures use simple illustrative assumptions; replace them with local, project-specific data before relying on them. The optional Pollinations link sends its prompt to a third-party image service. No database or user authentication is included, so this is a demonstration foundation rather than a production deployment for sensitive project data.