import os
import json
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any

import streamlit as st
from multimodal_suite import db
from multimodal_suite.ui_theme import inject_css, hero, AUTH_VISUAL
from multimodal_suite.offline_template import offline_template

try:
    from multimodal_suite import gemini_service
except Exception as e:
    gemini_service = None
    _gemini_import_error = str(e)
else:
    _gemini_import_error = None

try:
    from multimodal_suite import imagen_service
except Exception:
    imagen_service = None

try:
    from multimodal_suite import export
except Exception:
    export = None

st.set_page_config(
    page_title="Multimodal Content Generation Suite",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

PAGE_OPTIONS = {
    "Overview": "overview",
    "Create Campaign": "create_campaign",
    "Content Studio": "content_studio",
    "Visual Studio": "visual_studio",
    "Creative Analyzer": "creative_analyzer",
    "Campaign History": "campaign_history",
}

NAV_ICONS = {
    "overview": "◎",
    "create_campaign": "✦",
    "content_studio": "✎",
    "visual_studio": "◈",
    "creative_analyzer": "◉",
    "campaign_history": "☰",
}

def _hide_sidebar_css() -> str:
    """Return minimal CSS to hide the sidebar on the login page only."""
    return '<style>[data-testid="stSidebar"]{display:none!important;}</style>'

def _query_remember_token():
    if hasattr(st, "query_params"):
        token = st.query_params.get("remember")
        if isinstance(token, list):
            return token[0] if token else None
        return token
    params = st.experimental_get_query_params()
    values = params.get("remember", [])
    return values[0] if values else None


def _rerun() -> None:
    rerun_fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun")
    rerun_fn()


def _set_remember_token(token: Optional[str]) -> None:
    if hasattr(st, "query_params"):
        if token:
            st.query_params["remember"] = token
        elif "remember" in st.query_params:
            del st.query_params["remember"]
        return
    if token:
        st.experimental_set_query_params(remember=token)
    else:
        st.experimental_set_query_params()


def _init_session() -> None:
    if "page" not in st.session_state:
        st.session_state["page"] = "overview"
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "remember_token" not in st.session_state:
        st.session_state["remember_token"] = None
    if not st.session_state["authenticated"]:
        token = _query_remember_token()
        user = db.user_from_remember_token(token)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["user"] = user
            st.session_state["remember_token"] = token


def _login_user(user: db.User, remember: bool) -> None:
    st.session_state["authenticated"] = True
    st.session_state["user"] = user
    if remember:
        token = db.create_remember_token(user.id)
        st.session_state["remember_token"] = token
        _set_remember_token(token)
    else:
        db.revoke_remember_token(st.session_state.get("remember_token"))
        st.session_state["remember_token"] = None
        _set_remember_token(None)
    _rerun()


def _logout() -> None:
    db.revoke_remember_token(st.session_state.get("remember_token"))
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["remember_token"] = None
    st.session_state["page"] = "overview"
    _set_remember_token(None)
    _rerun()


def _parse_brief(brief):
    if not brief:
        return None
    if isinstance(brief, dict):
        return brief
    try:
        parsed = json.loads(brief)
        return parsed if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def render_auth() -> None:
    left, right = st.columns([1.12, 0.88], gap="large")
    with left:
        hero(
            "Multimodal Content Generation Suite",
            "Plan campaigns, write platform-ready copy, generate visuals, and analyze creative performance.",
            ["Campaign briefs", "Social copy", "Visual studio", "Creative analysis"],
            eyebrow="Creative AI Workspace",
            visual=AUTH_VISUAL,
        )

    with right:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        is_signup = st.session_state["auth_mode"] == "signup"
        st.markdown('<div class="auth-eyebrow">Welcome</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="auth-title">{"Create your workspace" if is_signup else "Sign in to continue"}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Local email and password authentication. Google sign-in and email recovery are not configured."
        )

        switch_cols = st.columns(2)
        with switch_cols[0]:
            if st.button("Sign in", use_container_width=True, key="goto_login"):
                st.session_state["auth_mode"] = "login"
                _rerun()
        with switch_cols[1]:
            if st.button("Create account", use_container_width=True, key="goto_signup"):
                st.session_state["auth_mode"] = "signup"
                _rerun()

        show_password = st.checkbox("Show password", value=False, key="show_password")
        pw_type = "default" if show_password else "password"

        with st.form("auth_form", clear_on_submit=False):
            if is_signup:
                display_name = st.text_input("Full name")
            else:
                display_name = ""
            email = st.text_input("Email", placeholder="you@studio.com")
            password = st.text_input("Password", type=pw_type, placeholder="At least 8 characters")
            confirm = ""
            if is_signup:
                confirm = st.text_input("Confirm password", type=pw_type)
            remember = False
            if not is_signup:
                remember = st.checkbox("Remember me on this browser")
            submitted = st.form_submit_button(
                "Create account" if is_signup else "Sign in",
                use_container_width=True,
            )

        if submitted:
            email_error = db.validate_email(email)
            if email_error:
                st.error(email_error)
            elif is_signup:
                password_error = db.validate_password(password, confirm)
                if password_error:
                    st.error(password_error)
                else:
                    try:
                        user = db.create_user(email, password, display_name)
                        _login_user(user, remember=False)
                    except ValueError as exc:
                        st.error(str(exc))
            else:
                if not password:
                    st.error("Please enter your password.")
                else:
                    user = db.authenticate_user(email, password)
                    if not user:
                        st.error("Those credentials do not match an account. Check your email and password, or create an account.")
                    else:
                        _login_user(user, remember=remember)

        st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar(user: db.User) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <h2>MCGS Studio</h2>
                <p>Create. Captivate. Convert.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Navigation")
        for label, key in PAGE_OPTIONS.items():
            icon = NAV_ICONS.get(key, "•")
            if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                st.session_state["page"] = key
                _rerun()
        st.markdown(
            f"""
            <div class="profile-box">
                <strong>{user.display_name}</strong><br/>
                <span>{user.email}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Log out", key="logout_btn", use_container_width=True):
            _logout()


def render_overview() -> None:
    campaigns = db.get_all_campaigns()
    generated_dir = Path(__file__).resolve().parent / "generated"
    visual_count = len(list(generated_dir.glob("*.png"))) if generated_dir.exists() else 0
    content_count = sum(1 for c in campaigns if c.brief)
    st.markdown(
        '<div class="page-hero"><h1>Overview</h1><p>Your campaign workspace at a glance.</p></div>',
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns(3)
    for col, title, value in zip(
        [col1, col2, col3],
        ["Total Campaigns", "Generated Content", "Generated Visuals"],
        [len(campaigns), content_count, visual_count],
    ):
        with col:
            st.markdown(
                f"<div class='metric-card'><h3>{title}</h3><p>{value}</p></div>",
                unsafe_allow_html=True,
            )
    st.subheader("Recent campaigns")
    if not campaigns:
        st.info("No campaigns yet. Create one from Create Campaign or Content Studio.")
    else:
        for camp in campaigns:
            created = (camp.created_at or "")[:16].replace("T", " ")
            snippet = (camp.description or "No description saved.")[:180]
            st.markdown(
                f"<div class='campaign-chip'><h4>{camp.name}</h4><p>{created} · {snippet}</p></div>",
                unsafe_allow_html=True,
            )




def render_create_campaign() -> None:
    st.markdown('<div class="page-hero"><h1>Create Campaign</h1><p>Build a campaign brief and save it to your creative library.</p></div>', unsafe_allow_html=True)
    with st.form("campaign_form"):
        product_name = st.text_input("Product name")
        product_desc = st.text_area("Product description")
        target_audience = st.text_input("Target audience")
        marketing_obj = st.text_input("Marketing objective")
        platforms = st.multiselect("Platform selection", ["Instagram", "Facebook", "LinkedIn", "X", "YouTube", "WhatsApp", "Threads", "TikTok", "Pinterest", "Snapchat", "Website"])
        brand_tone = st.selectbox("Brand tone", ["Professional", "Playful", "Luxury", "Eco-friendly", "Modern"])
        submitted = st.form_submit_button("Generate Campaign")
    if submitted:
        values = [product_name.strip(), product_desc.strip(), target_audience.strip(), marketing_obj.strip()]
        product_name, product_desc, target_audience, marketing_obj = values
        missing = [label for label, value in zip(
            ["Product name", "Product description", "Target audience", "Marketing objective"], values
        ) if not value]
        if not platforms:
            missing.append("Platform selection")
        if missing:
            st.error("Please complete: " + ", ".join(missing))
        else:
            brief = None
            ai_generated = False
            if gemini_service is None:
                st.warning("AI is busy right now. Showing an editable template. Edit it before use. It is not AI-generated.")
                brief = offline_template(product_name, product_desc, target_audience, marketing_obj, platforms, brand_tone)
                ai_generated = False
            else:
                with st.spinner("Creating your campaign brief..."):
                    try:
                        brief = gemini_service.generate_campaign_brief(
                            product_name, product_desc, target_audience, marketing_obj, platforms, brand_tone
                        )
                        ai_generated = True
                    except Exception as exc:
                        st.warning("AI is busy right now. Showing an editable template. Edit it before use. It is not AI-generated.")
                        brief = offline_template(product_name, product_desc, target_audience, marketing_obj, platforms, brand_tone)
                        ai_generated = False

            if brief:
                st.session_state["generated_brief"] = brief
                st.session_state["generated_brief_ai"] = ai_generated
                st.session_state["generated_brief_campaign_name"] = product_name
                if ai_generated:
                    try:
                        db.save_campaign(product_name, product_desc, brief)
                        st.session_state["generated_brief_saved"] = True
                    except Exception as exc:
                        st.session_state["generated_brief_saved"] = False
                        st.error(f"Brief created, but could not save it: {exc}")
                else:
                    st.session_state["generated_brief_saved"] = False
    if st.session_state.get("generated_brief"):
        if st.session_state.get("generated_brief_ai"):
            st.success("Gemini campaign brief generated successfully.")
            if st.session_state.get("generated_brief_saved"):
                st.success("Campaign saved to your library.")
        render_brief_details(st.session_state["generated_brief"])
        from multimodal_suite.local_engine import use_gemini
        if not use_gemini():
            st.caption("Generated by the built-in offline campaign engine (rule-based, not AI). Review and edit before publishing.")

def render_brief_details(brief: dict) -> None:
    st.subheader("Campaign Brief")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("**Headline**")
        st.caption(brief.get("headline", ""))
        st.download_button("Copy", data=brief.get("headline", ""), file_name="headline.txt", mime="text/plain")
    st.markdown("**Tagline**")
    st.caption(brief.get("tagline", ""))
    st.download_button("Copy", data=brief.get("tagline", ""), file_name="tagline.txt", mime="text/plain")
    st.markdown("**Product Description**")
    st.write(brief.get("product_description", ""))
    st.download_button("Copy", data=brief.get("product_description", ""), file_name="product_description.txt", mime="text/plain")
    st.markdown("**Social Media Captions**")
    for i, cap in enumerate(brief.get("captions", []), 1):
        st.write(f"* {cap}")
        st.download_button(f"Copy {i}", data=cap, file_name=f"caption_{i}.txt", mime="text/plain")
    st.markdown("**Hashtags**")
    st.write(", ".join(brief.get("hashtags", [])))
    st.download_button("Copy", data=", ".join(brief.get("hashtags", [])), file_name="hashtags.txt", mime="text/plain")
    st.markdown("**Calls to Action**")
    for i, cta in enumerate(brief.get("ctas", []), 1):
        st.write(f"* {cta}")
        st.download_button(f"Copy CTA {i}", data=cta, file_name=f"cta_{i}.txt", mime="text/plain")
    st.markdown("**Visual Concept**")
    st.write(brief.get("visual_concept", ""))
    st.download_button("Copy", data=brief.get("visual_concept", ""), file_name="visual_concept.txt", mime="text/plain")


def render_content_studio() -> None:
    st.markdown('<div class="page-hero"><h1>Campaign Content Studio</h1><p>Generate platform-ready copy for your next launch.</p></div>', unsafe_allow_html=True)
    with st.form("studio_form"):
        product_name = st.text_input("Product name", key="studio_product")
        product_desc = st.text_area("Product description", key="studio_desc")
        audience = st.text_input("Target audience", key="studio_audience")
        objective = st.text_input("Marketing objective", key="studio_objective")
        platforms = st.multiselect("Social media platforms", ["Instagram", "Facebook", "LinkedIn", "X"], key="studio_platforms")
        tone = st.selectbox("Brand tone", ["Professional", "Friendly", "Luxury", "Bold", "Minimal"], key="studio_tone")
        submitted = st.form_submit_button("Generate Content")
    if submitted:
        required = [product_name.strip(), product_desc.strip(), audience.strip(), objective.strip()]
        missing = [name for name, val in zip(["Product name", "Product description", "Target audience", "Marketing objective"], required) if not val]
        if not platforms: missing.append("Platforms")
        if missing:
            st.error("Please complete: " + ", ".join(missing))
        else:
            if gemini_service is None:
                st.error(_gemini_import_error or "Gemini service is not configured.")
            else:
                with st.spinner("Generating content..."):
                    try:
                        brief = gemini_service.generate_campaign_brief(*required, platforms, tone)
                        st.session_state["studio_brief"] = brief
                        try:
                            db.save_campaign(required[0], required[1], brief)
                            st.session_state["studio_saved"] = True
                        except Exception as exc:
                            st.session_state["studio_saved"] = False
                            st.error(f"Could not save campaign: {exc}")
                    except Exception as exc:
                        st.session_state["studio_brief"] = None
                        st.error(f"Gemini generation failed: {exc}")
    if st.session_state.get("studio_brief"):
        if st.session_state.get("studio_saved"):
            st.success("Content generated and saved.")
        render_brief_details(st.session_state["studio_brief"])
        from multimodal_suite.local_engine import use_gemini
        if not use_gemini():
            st.caption("Generated by the built-in offline campaign engine (rule-based, not AI). Review and edit before publishing.")

def render_visual_studio() -> None:
    st.markdown('<div class="page-hero"><h1>Visual Studio</h1><p>Create campaign artwork with Vertex AI Imagen when cloud access is configured.</p></div>', unsafe_allow_html=True)
    if imagen_service is None:
        st.info("Image generation module could not be loaded. Text campaigns and image analysis remain available.")
    with st.form("visual_form"):
        prompt = st.text_area("Describe the visual you want")
        style = st.selectbox("Visual style", ["Modern", "Retro", "Minimalist", "Vibrant", "Editorial"])
        aspect = st.selectbox("Aspect ratio", ["1:1", "4:5", "9:16", "16:9"])
        submitted = st.form_submit_button("Generate Image")
    if submitted:
        if not prompt.strip():
            st.error("Please enter an image prompt.")
        elif imagen_service is None:
            st.error("Imagen service is unavailable. Check the project setup.")
        else:
            try:
                with st.spinner("Generating image..."):
                    path = imagen_service.generate_image(prompt.strip(), style, aspect)
                st.session_state["last_generated_image"] = path
                st.success("Image generated.")
            except Exception as exc:
                st.error(f"Image generation could not complete: {exc}")
    image_path = st.session_state.get("last_generated_image")
    if image_path and Path(image_path).is_file():
        st.image(image_path, use_container_width=True)
        with open(image_path, "rb") as image_file:
            st.download_button("Download image", image_file.read(), file_name=Path(image_path).name, mime="image/png")

def render_creative_analyzer() -> None:
    hero(
        "Creative Analyzer",
        "Upload a visual and review Gemini’s creative analysis.",
        ["Vision AI", "Composition", "Color analysis", "Brand consistency"],
    )
    uploaded = st.file_uploader("Upload an image for analysis", type=["png", "jpg", "jpeg"])
    if uploaded:
        st.image(uploaded, use_container_width=True)
        if st.button("Analyze creative"):
            if not gemini_service:
                st.error("Gemini service is unavailable, so image analysis cannot run.")
                if _gemini_import_error:
                    st.caption(_gemini_import_error)
            else:
                with st.spinner("Analyzing creative..."):
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            tmp.write(uploaded.getvalue())
                            temp_path = tmp.name
                        st.session_state["creative_analysis"] = gemini_service.analyze_image(temp_path)
                    except Exception as exc:
                        st.error(str(exc))

    if st.session_state.get("creative_analysis"):
        analysis = st.session_state["creative_analysis"]
        st.subheader("Analysis Results")
        fields = [
            "composition",
            "color_combination",
            "product_visibility",
            "marketing_effectiveness",
            "brand_consistency",
            "improvement_suggestions",
        ]
        for field in fields:
            val = analysis.get(field)
            if val:
                st.subheader(field.replace("_", " ").title())
                if isinstance(val, list):
                    for item in val:
                        st.write(f"- {item}")
                else:
                    st.write(val)


def render_campaign_history() -> None:
    st.markdown(
        '<div class="page-hero"><h1>Campaign History</h1><p>Review and export campaigns stored in your local library.</p></div>',
        unsafe_allow_html=True,
    )
    campaigns = db.get_all_campaigns()
    if not campaigns:
        st.info("No campaigns saved yet.")
    for camp in campaigns:
        with st.expander(camp.name):
            st.caption(f"Created: {camp.created_at}")
            if camp.description:
                st.write(camp.description)
            if not camp.brief:
                st.write("No brief saved")
            else:
                parsed_brief = _parse_brief(camp.brief)
                if parsed_brief:
                    st.json(parsed_brief)
                else:
                    st.write(camp.brief)
            if st.button("Export PDF", key=f"pdf_{camp.id}"):
                if export is None:
                    st.warning("PDF export is not available in this installation.")
                else:
                    pdf_path = export.export_campaign_to_pdf(camp)
                    with open(pdf_path, "rb") as f:
                        st.download_button("Download PDF", f, file_name=os.path.basename(pdf_path))


def render_dashboard(user: db.User) -> None:
    render_sidebar(user)
    if _gemini_import_error and gemini_service is None:
        st.caption(f"Gemini service import error: {_gemini_import_error}")
    page = st.session_state["page"]
    if page == "overview":
        render_overview()
    elif page == "create_campaign":
        render_create_campaign()
    elif page == "content_studio":
        render_content_studio()
    elif page == "visual_studio":
        render_visual_studio()
    elif page == "creative_analyzer":
        render_creative_analyzer()
    elif page == "campaign_history":
        render_campaign_history()
    else:
        st.error("Unknown page")


_init_session()
if not st.session_state["authenticated"]:
    st.markdown(_hide_sidebar_css(), unsafe_allow_html=True)
    render_auth()
else:
    render_dashboard(st.session_state["user"])
