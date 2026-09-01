"""
UI components for the Marquee theme. Pure presentation — no API calls
happen here except through data already fetched by the caller.
"""

from typing import Callable, Optional

import streamlit as st

CATEGORY_LABELS = {
    "trending": "Trending Today",
    "popular": "Popular",
    "top_rated": "Top Rated",
    "now_playing": "Now Playing",
    "upcoming": "Upcoming",
}


def sprocket_divider() -> None:
    st.markdown('<div class="sprocket-divider"></div>', unsafe_allow_html=True)


def section_header(eyebrow: str, title: str) -> None:
    st.markdown(
        f"""
        <div class="section-head">
            <span class="section-eyebrow">{eyebrow}</span>
        </div>
        <div class="section-title">{title}</div>
        """,
        unsafe_allow_html=True,
    )


def hero(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-eyebrow">{eyebrow}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="state-panel">
            <div class="state-icon">{icon}</div>
            <div class="state-title">{title}</div>
            <div class="state-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def error_state(message: str) -> None:
    empty_state("⚠️", "Something didn't load", message)


def skeleton_grid(cols: int = 6, count: int = 12) -> None:
    rows = (count + cols - 1) // cols
    idx = 0
    for _ in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= count:
                break
            idx += 1
            with colset[c]:
                st.markdown(
                    """
                    <div class="skeleton-card">
                        <div class="skeleton-poster"></div>
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line short"></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _rating_label(vote_average) -> str:
    try:
        v = float(vote_average)
        if v > 0:
            return f"★ {v:.1f}"
    except (TypeError, ValueError):
        pass
    return "—"


def ticket_card(movie: dict, key: str, on_open: Callable[[int], None]) -> None:
    """Renders one movie as a ticket-stub card inside a bordered container."""
    tmdb_id = movie.get("tmdb_id")
    title = movie.get("title") or "Untitled"
    poster = movie.get("poster_url")
    year = (movie.get("release_date") or "")[:4]
    rating = _rating_label(movie.get("vote_average"))

    with st.container(border=True):
        if poster:
            st.markdown(
                f"""
                <div class="ticket-poster-wrap">
                    <img src="{poster}" alt="{title}" loading="lazy" />
                    <div class="ticket-badge">{rating}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="ticket-poster-wrap">
                    <div class="ticket-no-poster">🎞️<br/>No artwork</div>
                    <div class="ticket-badge">{rating}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<div class="ticket-perf"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ticket-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="ticket-meta">{year or "—"}</div>', unsafe_allow_html=True
        )

        st.markdown('<div class="ticket-cta">', unsafe_allow_html=True)
        if st.button("View details", key=f"{key}_open"):
            if tmdb_id:
                on_open(int(tmdb_id))
        st.markdown("</div>", unsafe_allow_html=True)


def poster_grid(
    cards: list,
    cols: int,
    key_prefix: str,
    on_open: Callable[[int], None],
    empty_message: str = "No movies to show here yet.",
) -> None:
    if not cards:
        empty_state("🎬", "Nothing to screen", empty_message)
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break
            movie = cards[idx]
            with colset[c]:
                ticket_card(movie, key=f"{key_prefix}_{r}_{c}_{idx}", on_open=on_open)
            idx += 1


def render_grid_with_loading(
    fetch_fn: Callable[[], tuple],
    cols: int,
    key_prefix: str,
    on_open: Callable[[int], None],
    skeleton_count: int = 12,
    empty_message: str = "No movies to show here yet.",
) -> Optional[list]:
    """Shows a skeleton grid, fetches data, then swaps in the real grid."""
    placeholder = st.empty()
    with placeholder.container():
        skeleton_grid(cols, skeleton_count)

    data, err = fetch_fn()

    with placeholder.container():
        if err or data is None:
            error_state(err or "Unknown error.")
            return None
        poster_grid(data, cols, key_prefix, on_open, empty_message=empty_message)
    return data


def to_cards_from_tfidf_items(tfidf_items: Optional[list]) -> list:
    cards = []
    for x in tfidf_items or []:
        tmdb = x.get("tmdb") or {}
        if tmdb.get("tmdb_id"):
            cards.append(
                {
                    "tmdb_id": tmdb["tmdb_id"],
                    "title": tmdb.get("title") or x.get("title") or "Untitled",
                    "poster_url": tmdb.get("poster_url"),
                    "release_date": tmdb.get("release_date"),
                    "vote_average": tmdb.get("vote_average"),
                }
            )
    return cards


def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    """
    Supports both API shapes:
      1) raw TMDB: {"results": [{id, title, poster_path, ...}]}
      2) list of cards: [{tmdb_id, title, poster_url, ...}]

    Returns (suggestions, cards) where suggestions is a list of
    (label, tmdb_id) tuples.
    """
    keyword_l = keyword.strip().lower()

    if isinstance(data, dict) and "results" in data:
        raw = data.get("results") or []
        raw_items = []
        for m in raw:
            title = (m.get("title") or "").strip()
            tmdb_id = m.get("id")
            poster_path = m.get("poster_path")
            if not title or not tmdb_id:
                continue
            raw_items.append(
                {
                    "tmdb_id": int(tmdb_id),
                    "title": title,
                    "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}"
                    if poster_path
                    else None,
                    "release_date": m.get("release_date", ""),
                    "vote_average": m.get("vote_average"),
                }
            )
    elif isinstance(data, list):
        raw_items = []
        for m in data:
            tmdb_id = m.get("tmdb_id") or m.get("id")
            title = (m.get("title") or "").strip()
            poster_url = m.get("poster_url")
            if not title or not tmdb_id:
                continue
            raw_items.append(
                {
                    "tmdb_id": int(tmdb_id),
                    "title": title,
                    "poster_url": poster_url,
                    "release_date": m.get("release_date", ""),
                    "vote_average": m.get("vote_average"),
                }
            )
    else:
        return [], []

    matched = [x for x in raw_items if keyword_l in x["title"].lower()]
    final_list = matched if matched else raw_items

    suggestions = []
    for x in final_list[:10]:
        year = (x.get("release_date") or "")[:4]
        label = f"{x['title']} ({year})" if year else x["title"]
        suggestions.append((label, x["tmdb_id"]))

    cards = final_list[:limit]
    return suggestions, cards
