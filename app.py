import json
import os
from typing import Any

import streamlit as st
from PIL import Image

from construction_platform import (
    analyze_image,
    assistant_reply,
    build_concept_prompt,
    estimate_project,
    format_inr,
    get_weather_advisory,
)
from domain import (
    CRACK_DEMO,
    SAFETY_DEMO,
    validate_crack_report,
    validate_safety_report,
)


st.set_page_config(
    page_title="Sitewise | Construction Intelligence",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
    :root { --ink:#17231f; --muted:#62706a; --line:#dfe6e1; --paper:#f5f7f3;
            --white:#ffffff; --green:#1f654e; --lime:#d6ed7b; --amber:#d78135; --red:#b7463d; }
    html, body, [class*="css"] { font-family:'Manrope', sans-serif; color:var(--ink); }
    .stApp { background:var(--paper); }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { background:#18241f; border-right:1px solid #2c3933; }
    [data-testid="stSidebar"] * { color:#eef2ed; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding:7px 8px; }
    [data-testid="stSidebar"] [data-testid="stExpander"] { border-color:#38453f; }
    .brand { font-weight:800; font-size:21px; letter-spacing:0; margin:4px 0 0; }
    .brand-mark { display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px;
                  color:#17231f; background:var(--lime); border-radius:6px; margin-right:8px; font-size:13px; }
    .sidebar-note { color:#a9b6ae; font-size:12px; line-height:1.6; }
    .eyebrow { color:var(--green); font-family:'DM Mono',monospace; font-size:11px; text-transform:uppercase;
               letter-spacing:0; font-weight:500; }
    .page-title { font-size:30px; font-weight:800; letter-spacing:0; margin:3px 0 4px; }
    .page-subtitle { color:var(--muted); font-size:14px; margin-bottom:22px; }
    .section-label { font-family:'DM Mono',monospace; color:var(--muted); font-size:11px; text-transform:uppercase;
                     letter-spacing:0; margin:18px 0 8px; }
    .notice { border-left:3px solid var(--amber); background:#fff7e9; padding:12px 14px; border-radius:0 5px 5px 0;
              font-size:13px; color:#573c20; margin:10px 0 16px; }
    .demo-banner { border-left:3px solid #6a8778; background:#eaf0eb; padding:10px 13px; border-radius:0 5px 5px 0;
                   font-size:12px; color:#31433a; margin:8px 0 14px; }
    .stat-label { font-family:'DM Mono',monospace; color:var(--muted); font-size:10px; text-transform:uppercase; }
    .stButton > button, .stDownloadButton > button, .stLinkButton > a { border-radius:5px; font-weight:700; }
    .stButton > button[kind="primary"] { background:#1f654e; border-color:#1f654e; }
    div[data-testid="stMetric"] { background:white; padding:13px 16px; border:1px solid var(--line); border-radius:5px; }
    div[data-testid="stMetricLabel"] { color:var(--muted); }
    div[data-testid="stMetricValue"] { color:var(--ink); }
    .stProgress > div > div > div > div { background:#1f654e; }
    h1, h2, h3 { letter-spacing:0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def page_heading(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="eyebrow">{eyebrow}</div><div class="page-title">{title}</div>'
        f'<div class="page-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def report_download(report: dict[str, Any], label: str, filename: str) -> None:
    st.download_button(
        label,
        data=json.dumps(report, indent=2, ensure_ascii=True),
        file_name=filename,
        mime="application/json",
        use_container_width=True,
    )


def load_image(upload: Any) -> tuple[bytes, str]:
    image_bytes = upload.getvalue()
    with Image.open(upload) as image:
        image.verify()
    mime_type = "image/png" if upload.type == "image/png" else "image/jpeg"
    return image_bytes, mime_type


def render_safety(api_key: str, model: str) -> None:
    page_heading(
        "Field intelligence / 01",
        "Site safety audit",
        "Review visible PPE and site conditions from a photo. Treat findings as a prompt for a qualified on-site inspection.",
    )
    st.markdown(
        '<div class="notice">A photo cannot confirm hidden conditions or reliably identify every worker. '
        'Do not use this advisory as a substitute for a competent person, applicable Indian requirements, or OSHA rules.</div>',
        unsafe_allow_html=True,
    )
    upload = st.file_uploader("Upload a site photo", type=["jpg", "jpeg", "png"], key="safety_image")
    if upload:
        st.image(upload, caption=upload.name, use_container_width=True)
        if st.button("Run PPE and hazard review", type="primary", key="run_safety"):
            try:
                image_bytes, mime_type = load_image(upload)
                with st.spinner("Reviewing visible site conditions..."):
                    result = analyze_image("safety", image_bytes, mime_type, api_key, model)
                st.session_state["safety_report"] = validate_safety_report(result)
                st.session_state["safety_demo"] = not bool(api_key)
            except Exception as exc:
                st.error(f"Could not analyze this image: {exc}")
    report = st.session_state.get("safety_report")
    if report:
        if st.session_state.get("safety_demo"):
            st.markdown('<div class="demo-banner">Demonstration output only. It was not derived from the uploaded image.</div>', unsafe_allow_html=True)
        left, right = st.columns([1, 2])
        left.metric("Safety score", f"{report['safety_score']} / 100")
        right.metric("Overall status", report["overall_status"])
        st.markdown('<div class="section-label">PPE checklist</div>', unsafe_allow_html=True)
        st.dataframe(report["ppe_detection"], use_container_width=True, hide_index=True)
        st.markdown('<div class="section-label">Site hazards</div>', unsafe_allow_html=True)
        if report["hazards"]:
            for hazard in report["hazards"]:
                st.warning(f"{hazard['severity']} | {hazard['hazard']}\n\n{hazard['corrective_action']}")
        else:
            st.info("No hazards were returned. Absence of a reported hazard does not establish a safe site.")
        st.caption(report["summary"])
        report_download(report, "Download safety report", "site-safety-report.json")


def render_cracks(api_key: str, model: str) -> None:
    page_heading(
        "Field intelligence / 02",
        "Crack diagnostics",
        "Capture a visible defect and organize observations for a structural engineer's review.",
    )
    st.markdown(
        '<div class="notice">Image-based crack classification and width estimates are approximate. '
        'Do not infer structural safety from this result; arrange an in-person assessment for active, wide, or load-bearing cracks.</div>',
        unsafe_allow_html=True,
    )
    upload = st.file_uploader("Upload a concrete or wall image", type=["jpg", "jpeg", "png"], key="crack_image")
    if upload:
        st.image(upload, caption=upload.name, use_container_width=True)
        if st.button("Assess visible crack", type="primary", key="run_crack"):
            try:
                image_bytes, mime_type = load_image(upload)
                with st.spinner("Preparing a diagnostic summary..."):
                    result = analyze_image("crack", image_bytes, mime_type, api_key, model)
                st.session_state["crack_report"] = validate_crack_report(result)
                st.session_state["crack_demo"] = not bool(api_key)
            except Exception as exc:
                st.error(f"Could not analyze this image: {exc}")
    report = st.session_state.get("crack_report")
    if report:
        if st.session_state.get("crack_demo"):
            st.markdown('<div class="demo-banner">Demonstration output only. It was not derived from the uploaded image.</div>', unsafe_allow_html=True)
        one, two, three = st.columns(3)
        one.metric("Defect category", report["defect_type"])
        two.metric("Estimated width", f"{report['estimated_width_mm']:.1f} mm" if report["estimated_width_mm"] is not None else "Unknown")
        three.metric("Urgency", report["urgency"])
        st.markdown("**Observed notes**")
        st.write(report["observations"])
        st.markdown("**Potential causes**")
        for cause in report["probable_causes"]:
            st.write(f"- {cause}")
        st.markdown("**Repair options for engineering review**")
        for repair in report["recommended_repairs"]:
            st.write(f"- {repair}")
        if report["engineer_review_required"]:
            st.warning("Professional structural review is recommended before selecting a repair.")
        report_download(report, "Download crack report", "crack-diagnostics-report.json")


def render_planning() -> None:
    page_heading(
        "Project intelligence / 03",
        "Planning and valuation",
        "Build a first-pass budget and materials snapshot from area, asset type, and market tier.",
    )
    st.markdown(
        '<div class="notice">Indicative planning benchmarks only, not a contractor quote or formal property valuation. '
        'Local rates, specifications, taxes, land value, and site conditions can materially change results.</div>',
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns(2)
    with col_a:
        structure = st.selectbox("Structure type", ["Residential", "Commercial", "Industrial"])
        area = st.number_input("Built-up area (sq ft)", min_value=100, max_value=2_000_000, value=1800, step=100)
    with col_b:
        tier = st.selectbox("Location tier", ["Tier 1", "Tier 2", "Tier 3"])
        completion = st.slider("Completion", min_value=0, max_value=100, value=35, format="%d%%")
    estimate = estimate_project(structure, area, tier, completion)
    st.markdown('<div class="section-label">Indicative project snapshot / INR</div>', unsafe_allow_html=True)
    first, second, third = st.columns(3)
    first.metric("Estimated project budget", format_inr(estimate["total_budget_inr"]))
    second.metric("Capital expenditure to date", format_inr(estimate["capex_incurred_inr"]))
    third.metric("Indicative market value", format_inr(estimate["market_value_inr"]))
    progress_left, progress_right = st.columns([2, 1])
    with progress_left:
        st.caption(f"Milestone completion: {completion}%")
        st.progress(completion / 100)
    with progress_right:
        st.metric("Steel allowance", f"{estimate['steel_kg']:,.0f} kg")
        st.metric("Cement allowance", f"{estimate['cement_bags']:,.0f} bags")
    st.caption("Material quantities use broad built-up-area allowances and exclude design-specific detailing and wastage adjustments.")

    st.markdown('<div class="section-label">Concept visualization</div>', unsafe_allow_html=True)
    prompt = build_concept_prompt(structure, area, tier)
    st.text_area("Image generation prompt", prompt, height=95, disabled=True)
    from urllib.parse import quote

    image_url = f"https://image.pollinations.ai/prompt/{quote(prompt, safe='')}?width=1024&height=768&model=flux&nologo=true"
    st.link_button("Open conceptual render", image_url)
    st.caption("The linked third-party image service receives the prompt. Renderings are conceptual, not construction documents.")


def render_assistant(api_key: str, model: str) -> None:
    page_heading(
        "Field intelligence / 04",
        "Daily site assistant",
        "Pair a weather condition with a practical site protocol, then ask a construction question.",
    )
    weather = st.selectbox("Today's weather", ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"])
    advisory = get_weather_advisory(weather)
    st.markdown(f"### {advisory['title']}")
    st.write(advisory["summary"])
    for item in advisory["actions"]:
        st.write(f"- {item}")
    st.caption("Weather advisories are general prompts. Follow site-specific plans, equipment limits, and official forecasts.")
    st.markdown('<div class="section-label">Construction knowledge assistant</div>', unsafe_allow_html=True)
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Ask about planning, materials, sequencing, or site practice")
    if question:
        st.session_state["chat_history"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        try:
            with st.spinner("Preparing a response..."):
                answer = assistant_reply(question, weather, st.session_state["chat_history"], api_key, model)
            st.session_state["chat_history"].append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)
            if not api_key:
                st.caption("Demonstration response: add a Groq API key in the sidebar for model-backed assistance.")
        except Exception as exc:
            st.error(f"Assistant request failed: {exc}")


with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">S</span>SITEWISE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-note">Construction intelligence / field decision support</div>', unsafe_allow_html=True)
    st.markdown("---")
    key_from_env = os.getenv("GROQ_API_KEY", "")
    api_key = st.text_input(
        "Groq API key",
        value=key_from_env,
        type="password",
        help="Kept in this Streamlit session only. Or set GROQ_API_KEY before launch.",
    )
    model = st.text_input(
        "Groq model",
        value=os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"),
        key="groq_model",
    )
    if api_key:
        st.success("Model mode enabled")
    else:
        st.info("Demo mode / no API key")
    st.markdown("---")
    page = st.radio(
        "WORKSPACE",
        ["Site safety audit", "Crack diagnostics", "Planning & valuation", "Daily site assistant"],
        label_visibility="visible",
    )
    with st.expander("Architecture overview"):
        st.markdown(
            '<div class="sidebar-note">Streamlit UI → Groq vision-language model → locally validated JSON reports. '
            'Planning estimates run locally. No database or uploaded-file persistence.</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="sidebar-note">Advisory tool only. Verify decisions with qualified professionals.</div>', unsafe_allow_html=True)


if page == "Site safety audit":
    render_safety(api_key, model)
elif page == "Crack diagnostics":
    render_cracks(api_key, model)
elif page == "Planning & valuation":
    render_planning()
else:
    render_assistant(api_key, model)