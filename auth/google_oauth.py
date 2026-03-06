from __future__ import annotations
import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from config.settings import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
)


def _get_client_config() -> dict:
    return {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }


def get_oauth_flow() -> Flow:
    flow = Flow.from_client_config(
        _get_client_config(),
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    return flow


def get_authorization_url() -> str:
    flow = get_oauth_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    st.session_state["oauth_state"] = state
    return auth_url


def exchange_code_for_credentials(authorization_code: str) -> Credentials:
    flow = get_oauth_flow()
    flow.fetch_token(code=authorization_code)
    return flow.credentials


def get_authenticated_credentials() -> Credentials | None:
    creds = st.session_state.get("google_credentials")
    if creds is None:
        return None

    if isinstance(creds, dict):
        creds = Credentials(
            token=creds.get("token"),
            refresh_token=creds.get("refresh_token"),
            token_uri=creds.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=creds.get("client_id", GOOGLE_CLIENT_ID),
            client_secret=creds.get("client_secret", GOOGLE_CLIENT_SECRET),
            scopes=creds.get("scopes", GOOGLE_SCOPES),
        )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _store_credentials(creds)
        except Exception:
            st.session_state.pop("google_credentials", None)
            return None

    return creds


def _store_credentials(creds: Credentials) -> None:
    st.session_state["google_credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else GOOGLE_SCOPES,
    }


def handle_oauth_callback() -> bool:
    params = st.experimental_get_query_params()
    code = params.get("code")
    if not code:
        return False

    # experimental_get_query_params returns dict of lists
    if isinstance(code, list):
        code = code[0]

    try:
        creds = exchange_code_for_credentials(code)
        _store_credentials(creds)
        st.experimental_set_query_params()
        return True
    except Exception as e:
        st.error(f"OAuth authentication failed: {e}")
        return False


def render_login_ui() -> None:
    st.markdown("## Connect to Google Search Console")
    st.markdown(
        "Authenticate with your Google account to access Search Console data."
    )

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        st.error(
            "Google OAuth credentials not configured. "
            "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file."
        )
        return

    auth_url = get_authorization_url()
    st.markdown(
        f'<a href="{auth_url}" target="_self" style="display:inline-block;padding:0.5em 1em;'
        f'background-color:#4CAF50;color:white;text-decoration:none;border-radius:4px;">'
        f'Connect Google Search Console</a>',
        unsafe_allow_html=True,
    )


def logout() -> None:
    for key in ["google_credentials", "selected_property", "analysis_complete",
                "gsc_data", "opportunities", "user_page_data", "serp_results",
                "intent_data", "competitor_data", "gap_analyses", "actions"]:
        st.session_state.pop(key, None)
