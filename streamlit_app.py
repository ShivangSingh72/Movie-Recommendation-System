import streamlit as st

import api
from components import (
    CATEGORY_LABELS,
    empty_state,
    error_state,
    hero,
    parse_tmdb_search_to_cards,
    poster_grid,
    render_grid_with_loading,
    section_header,
    sprocket_divider,
    to_cards_from_tfidf_items,
)
from theme import inject_base_css

st.set_page_config(page_title=" — Movie Recommender — ", page_icon="🎟️", layout="wide")
inject_base_css()

# =============================================================================
# ROUTING (single-file, query-param backed — same pattern as before)
# =============================================================================
if "view" not in st.session_state:
    st.session_state.view = "home"  # home | details
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

qp_view = st.query_params.get("view")
qp_id = st.query_params.get("id")
if qp_view in ("home", "details"):
    st.session_state.view = qp_view
if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except ValueError:
        pass


def goto_home() -> None:
    st.session_state.view = "home"
    st.query_params["view"] = "home"
    if "id" in st.query_params:
        del st.query_params["id"]
    st.rerun()


def goto_details(tmdb_id: int) -> None:
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.query_params["view"] = "details"
    st.query_params["id"] = str(int(tmdb_id))
    st.rerun()


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown(
        '<div class="nav-wordmark">MOVIE<span>MANIAQ</span></div>'
        '<div class="nav-tagline">Now Screening</div>',
        unsafe_allow_html=True,
    )

    if st.button("🏠  Home", use_container_width=True):
        goto_home()

    st.markdown('<div class="nav-eyebrow">Browse</div>', unsafe_allow_html=True)
    home_category = st.selectbox(
        "Category",
        list(CATEGORY_LABELS.keys()),
        format_func=lambda k: CATEGORY_LABELS[k],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown('<div class="nav-eyebrow">Layout</div>', unsafe_allow_html=True)
    grid_cols = st.slider("Grid columns", 3, 8, 6, label_visibility="collapsed")

    st.markdown("---")
    st.markdown(
        '<span class="small-muted">Posters &amp; details via TMDB · '
        "recommendations via local TF-IDF</span>",
        unsafe_allow_html=True,
    )

# =============================================================================
# VIEW: HOME
# =============================================================================
if st.session_state.view == "home":
    hero(
        eyebrow="Tonight's Showing",
        title="Find your next favorite film.",
        subtitle=(
            "Search a title for instant matches, or browse what's trending, "
            "popular, and newly released — then open a film for tailored "
            "recommendations."
        ),
    )
    sprocket_divider()

    typed = st.text_input(
        "Search",
        placeholder="Search by title — try “batman”, “inception”, “love”…",
        label_visibility="collapsed",
    )

    if typed.strip():
        if len(typed.strip()) < 2:
            st.caption("Type at least 2 characters to search the box office.")
        else:
            data, err = api.tmdb_search(typed.strip())

            if err or data is None:
                error_state(err or "Search failed.")
            else:
                suggestions, cards = parse_tmdb_search_to_cards(
                    data, typed.strip(), limit=24
                )

                if suggestions:
                    labels = ["Jump to a match…"] + [s[0] for s in suggestions]
                    selected = st.selectbox("Suggestions", labels, index=0)
                    if selected != "Jump to a match…":
                        label_to_id = {s[0]: s[1] for s in suggestions}
                        goto_details(label_to_id[selected])

                section_header("Search Results", f'Matches for "{typed.strip()}"')
                poster_grid(
                    cards,
                    cols=grid_cols,
                    key_prefix="search_results",
                    on_open=goto_details,
                    empty_message="No titles matched that search. Try another keyword.",
                )
        st.stop()

    section_header("Now Showing", CATEGORY_LABELS[home_category])
    render_grid_with_loading(
        fetch_fn=lambda: api.get_home(home_category, limit=24),
        cols=grid_cols,
        key_prefix="home_feed",
        on_open=goto_details,
        skeleton_count=grid_cols * 2,
        empty_message="This category is empty right now.",
    )

# =============================================================================
# VIEW: DETAILS
# =============================================================================
elif st.session_state.view == "details":
    tmdb_id = st.session_state.selected_tmdb_id

    if not tmdb_id:
        empty_state("🎟️", "No film selected", "Head back to the lobby and pick something to watch.")
        if st.button("← Back to Home"):
            goto_home()
        st.stop()

    if st.button("← Back to Home"):
        goto_home()

    data, err = api.get_movie_details(tmdb_id)
    if err or not data:
        error_state(err or "Could not load this title.")
        st.stop()

    title = data.get("title", "")
    genres = [g["name"] for g in data.get("genres", [])]
    release = data.get("release_date") or "—"

    if data.get("backdrop_url"):
        st.markdown(
            f"""
            <div class="detail-backdrop">
                <img src="{data['backdrop_url']}" alt="{title} backdrop"/>
                <div class="detail-backdrop-overlay"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    left, right = st.columns([1, 2.3], gap="large")

    with left:
        with st.container(border=True):
            if data.get("poster_url"):
                st.markdown(
                    f"""<div class="ticket-poster-wrap">
                    <img src="{data['poster_url']}" alt="{title}"/>
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="ticket-poster-wrap"><div class="ticket-no-poster">'
                    "🎞️<br/>No artwork</div></div>",
                    unsafe_allow_html=True,
                )

    with right:
        st.markdown('<div class="detail-eyebrow">Feature Presentation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-title">{title}</div>', unsafe_allow_html=True)

        pills = [f'<span class="pill">{release}</span>']
        for g in genres[:4]:
            pills.append(f'<span class="pill">{g}</span>')
        st.markdown(f'<div class="detail-meta-row">{"".join(pills)}</div>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="detail-overview">{data.get("overview") or "No synopsis available."}</div>',
            unsafe_allow_html=True,
        )

    sprocket_divider()

    if title.strip():
        bundle, err2 = api.get_search_bundle(title.strip(), tfidf_top_n=12, genre_limit=12)

        if not err2 and bundle:
            section_header("Because You Watched This", "Similar in Story")
            poster_grid(
                to_cards_from_tfidf_items(bundle.get("tfidf_recommendations")),
                cols=grid_cols,
                key_prefix="details_tfidf",
                on_open=goto_details,
                empty_message="No close story matches in the local catalog.",
            )

            st.markdown("<div style='height: 0.6rem'></div>", unsafe_allow_html=True)
            section_header("More Like This", "Same Genre, New Picks")
            poster_grid(
                bundle.get("genre_recommendations", []),
                cols=grid_cols,
                key_prefix="details_genre",
                on_open=goto_details,
                empty_message="No genre matches found.",
            )
        else:
            section_header("More Like This", "Same Genre")
            genre_only, err3 = api.get_recommend_genre(tmdb_id, limit=18)
            if not err3 and genre_only:
                poster_grid(
                    genre_only,
                    cols=grid_cols,
                    key_prefix="details_genre_fallback",
                    on_open=goto_details,
                )
            else:
                empty_state("🎬", "No recommendations yet", "Try another title from the lobby.")
    else:
        empty_state("🎬", "No recommendations yet", "This title has no name to match against.")
