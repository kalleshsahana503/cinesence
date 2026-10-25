import time
import streamlit as st
import requests
import textwrap

API_URL = "http://localhost:8000"
APP_NAME = "CineSense"

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

GENRE_OPTIONS = [
    "Romance", "Drama", "Thriller", "Horror", "Comedy",
    "Action", "Crime", "Documentary", "Family",
]

LANGUAGE_ROWS = [
    ("kn", "Kannada"),
    ("en", "English"),
    ("hi", "Hindi"),
    ("mr", "Marathi"),
]

LOADING_MESSAGES = [
    "🎞️ Unspooling the film reel...",
    "🍿 Popping the popcorn...",
    "🎬 Scanning the archives...",
    "✨ Matching moods to movies...",
]

# ---------------------------------------------------------------------------
# THEME: black main area + galaxy sidebar + extra animation
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background: #000000; color: #f0e9ff; }
    #MainMenu, footer, header { visibility: hidden; }

    .floaty {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none; z-index: 0; overflow: hidden;
    }
    .floaty span {
        position: absolute; font-size: 22px; opacity: 0.35;
        animation: floatUp linear infinite, twinkle 3s ease-in-out infinite;
    }
    @keyframes floatUp {
        0%   { transform: translateY(0) rotate(0deg); }
        100% { transform: translateY(-110vh) rotate(25deg); }
    }
    @keyframes twinkle {
        0%, 100% { opacity: 0.15; }
        50% { opacity: 0.5; }
    }

    section.main > div { position: relative; z-index: 1; }

    .app-title {
        font-size: 34px; font-weight: 800; margin: 6px 0 18px 0;
        background: linear-gradient(90deg, #ff3b3b, #ffffff, #ff3b3b);
        background-size: 200% auto;
        -webkit-background-clip: text; background-clip: text; color: transparent;
        animation: titleShine 6s linear infinite;
        display: inline-block;
    }
    @keyframes titleShine {
        0% { background-position: 0% center; }
        100% { background-position: 200% center; }
    }

    .hero {
        position: relative; width: 100%; border-radius: 16px; overflow: hidden;
        margin-bottom: 4px; min-height: 380px; background-size: cover;
        background-position: center; display: flex; align-items: flex-end;
        box-shadow: 0 8px 30px rgba(255,255,255, 0.08);
        animation: heroFade 0.6s ease;
    }
    @keyframes heroFade {
        from { opacity: 0; transform: scale(0.98); }
        to { opacity: 1; transform: scale(1); }
    }
    .hero-overlay {
        width: 100%; padding: 32px;
        background: linear-gradient(0deg, rgba(0,0,0,0.92) 5%, rgba(0,0,0,0.55) 55%, rgba(0,0,0,0.05) 100%);
    }
    .hero-title { font-size: 42px; font-weight: 800; margin-bottom: 8px; color: #ffffff !important; }
    .hero-meta { color: #e6d9ff; font-size: 15px; margin-bottom: 12px; }
    .hero-overview { max-width: 640px; color: #f3ecff; font-size: 15px; }

    div[class*="st-key-hero_container"] { position: relative; }
    div[class*="st-key-hero_next_btn"] {
        position: absolute; top: 18px; right: 18px; z-index: 5; width: 46px;
    }
    div[class*="st-key-hero_next_btn"] button {
        opacity: 0.18; background: rgba(255,255,255,0.15); color: white;
        border-radius: 50%; width: 46px; height: 46px; font-size: 20px;
        border: 1px solid rgba(255,255,255,0.5); transition: opacity 0.2s ease;
    }
    div[class*="st-key-hero_next_btn"] button:hover { opacity: 1; background: rgba(255,255,255,0.35); }

    .row-title {
        font-size: 20px !important; font-weight: 800 !important; margin: 26px 0 10px 2px !important;
        color: #ff3b3b !important;
    }

    .hscroll {
        display: flex; overflow-x: auto; gap: 14px; padding-bottom: 12px;
        scrollbar-width: thin; scrollbar-color: #ffffff #000000;
    }
    .hscroll::-webkit-scrollbar { height: 7px; }
    .hscroll::-webkit-scrollbar-thumb { background: #ffffff; border-radius: 4px; }

    .hcard {
        flex: 0 0 150px; text-decoration: none; color: inherit;
        animation: cardIn 0.4s ease both;
    }
    @keyframes cardIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .hcard img {
        width: 150px; height: 225px; object-fit: cover; border-radius: 10px;
        transition: transform 0.2s ease, box-shadow 0.2s ease; display: block;
        border: 1px solid #2a1f3d; background: #111;
    }
    .hcard:hover img { transform: scale(1.06); box-shadow: 0 8px 20px rgba(255,255,255,0.5); border-color:#ffffff; }
    .hcard .t {
        font-size: 12.5px; margin-top: 6px; color: #ffffff; font-weight: 600;
        max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .hcard .m { font-size: 11px; color: #b399e0; }
    .hcard .w {
        font-size: 10.5px; color: #8f7bb0; max-width: 150px; white-space: normal;
        line-height: 1.3; margin-top: 2px;
    }
    .new-badge {
        display: inline-block; background: #ff3b3b; color: white; font-size: 9px;
        font-weight: 700; padding: 1px 6px; border-radius: 8px; margin-left: 4px;
    }

    div.stButton > button {
        background-color: #ffffff; color: #000000; border: none; border-radius: 6px;
        transition: box-shadow 0.3s ease;
    }
    div.stButton > button:hover { background-color: #e5e5e5; color: #000000; }
    div[class*="st-key-recommend_btn"] button {
        animation: pulseGlow 2.2s ease-in-out infinite;
    }
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 0px rgba(255,59,59,0.0); }
        50% { box-shadow: 0 0 16px rgba(255,59,59,0.55); }
    }

    input[type="text"] { background-color: #1a1a1a !important; color: #f0e9ff !important; }

    .loading-wrap { display: flex; align-items: center; gap: 10px; margin: 10px 0; }
    .loading-reel {
        font-size: 26px; animation: spinReel 1.1s linear infinite;
        display: inline-block;
    }
    @keyframes spinReel {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .loading-text { color: #ff8080; font-weight: 600; }

    /* ---- Galaxy sidebar ---- */
    section[data-testid="stSidebar"] {
        background:
            linear-gradient(115deg, transparent 0%, transparent 28%, rgba(130,90,190,0.28) 42%, rgba(190,150,230,0.4) 50%, rgba(100,70,170,0.28) 58%, transparent 72%, transparent 100%),
            radial-gradient(ellipse at 50% 50%, #0d0a1f 0%, #060412 55%, #020103 100%);
        position: relative;
        overflow: hidden;
    }
    section[data-testid="stSidebar"] > div { position: relative; z-index: 2; }

    .sidebar-sky {
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none; overflow: hidden; z-index: 0;
    }
    .sidebar-sky .star {
        position: absolute; border-radius: 50%; background: #ffffff;
        animation: skyTwinkle ease-in-out infinite;
    }
    .sidebar-sky .star.blue { background: #a6c8ff; }
    .sidebar-sky .star.pink { background: #ffb3d9; }
    .sidebar-sky .shooting-star {
        position: absolute; width: 90px; height: 2px;
        background: linear-gradient(90deg, #ffffff, rgba(255,255,255,0));
        transform: rotate(-30deg);
        animation: shoot linear infinite;
        opacity: 0;
    }
    @keyframes skyTwinkle {
        0%, 100% { opacity: 0.15; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.3); }
    }
    @keyframes shoot {
        0%   { opacity: 0; transform: translate(0, 0) rotate(-30deg); }
        5%   { opacity: 1; }
        20%  { opacity: 0; transform: translate(-260px, 150px) rotate(-30deg); }
        100% { opacity: 0; }
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] label p,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stMultiSelect label {
        color: #8b0000 !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h1 *,
    section[data-testid="stSidebar"] h2 *,
    section[data-testid="stSidebar"] h3 * {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.8);
    }
    </style>

    <div class="floaty">
        <span style="left:5%; top:80%; animation-duration:14s;">✨</span>
        <span style="left:15%; top:90%; animation-duration:18s;">⭐</span>
        <span style="left:25%; top:75%; animation-duration:12s;">😊</span>
        <span style="left:38%; top:95%; animation-duration:20s;">🌟</span>
        <span style="left:50%; top:85%; animation-duration:16s;">😄</span>
        <span style="left:62%; top:92%; animation-duration:13s;">✨</span>
        <span style="left:74%; top:80%; animation-duration:19s;">⭐</span>
        <span style="left:85%; top:88%; animation-duration:15s;">😊</span>
        <span style="left:93%; top:78%; animation-duration:17s;">🌟</span>
        <span style="left:8%; top:70%; animation-duration:22s;">😄</span>
    </div>
    """,
    unsafe_allow_html=True,
)


def poster_or_placeholder(url):
    return url if url else "https://placehold.co/300x450/111111/ffffff?text=No+Poster"


def shared_genre_reason(origin_genres: str, candidate_genres: str, candidate_title: str) -> str:
    origin_set = set((origin_genres or "").split("|")) - {""}
    cand_set = set((candidate_genres or "").split("|")) - {""}
    shared = origin_set & cand_set
    if shared:
        return f"Shares {', '.join(sorted(shared))} with {candidate_title}"
    return "Similar plot and themes"


def render_hscroll_row(title, movies):
    if not movies:
        return
    st.markdown(f"<div class='row-title'>{title}</div>", unsafe_allow_html=True)
    cards = []
    for i, m in enumerate(movies):
        rating = m.get("vote_average")
        rating_txt = f"★ {float(rating):.1f}" if rating else ""
        year = m.get("release_year", m.get("year", ""))
        year_txt = f"· {year}" if year else ""
        why_html = f'<div class="w">{m["why"]}</div>' if m.get("why") else ""
        new_badge = '<span class="new-badge">NEW</span>' if m.get("is_new") else ""
        card = (
            f'<a class="hcard" href="?movie_id={m["id"]}" target="_self" style="animation-delay:{i*0.04}s;">'
            f'<img src="{poster_or_placeholder(m.get("poster_url"))}" />'
            f'<div class="t">{m["title"]}{new_badge}</div>'
            f'<div class="m">{rating_txt} {year_txt}</div>'
            f'{why_html}'
            f'</a>'
        )
        cards.append(card)
    st.markdown(f"<div class='hscroll'>{''.join(cards)}</div>", unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False)
def cached_get(url, params_tuple=()):
    try:
        r = requests.get(url, params=dict(params_tuple), timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"__error__": str(e)}


def safe_get(url, **kwargs):
    params = kwargs.get("params", {})
    return cached_get(url, params_tuple=tuple(sorted(params.items())))


def matches_genres(movie, selected_genres):
    if not selected_genres:
        return True
    movie_genres = (movie.get("genres") or "").split("|")
    return any(g in movie_genres for g in selected_genres)


def render_hero(movie, key=None, cyclable=False):
    backdrop = movie.get("backdrop_url") or movie.get("poster_url")
    if not backdrop:
        return
    container = st.container(key="hero_container") if cyclable else st.container()
    with container:
        st.markdown(
            textwrap.dedent(f"""
            <div class="hero" style="background-image:url('{backdrop}');">
              <div class="hero-overlay">
                <div class="hero-title">{movie['title']}</div>
                <div class="hero-meta">
                    {"★ " + f"{float(movie['vote_average']):.1f}" if movie.get('vote_average') else ""}
                    &nbsp;·&nbsp; {movie.get('release_year','')}
                    &nbsp;·&nbsp; {movie.get('genres','')}
                </div>
                <div class="hero-overview">{(movie.get('overview') or '')[:280]}</div>
              </div>
            </div>
            """).strip(),
            unsafe_allow_html=True,
        )
        if cyclable:
            if st.button("→", key=key, help="Show next popular movie"):
                st.session_state.hero_manual_offset = st.session_state.get("hero_manual_offset", 0) + 1
                st.rerun()


params = st.query_params
selected_movie = params.get("movie_id")

# ============================================================================
# DETAIL PAGE
# ============================================================================
if selected_movie:
    if st.button("← Back"):
        st.query_params.clear()
        st.rerun()

    detail = safe_get(f"{API_URL}/movie/{selected_movie}")

    if "__error__" in detail:
        st.error(f"Couldn't reach backend: {detail['__error__']}")
    elif "title" not in detail:
        st.warning(detail.get("detail", "Movie not found."))
    else:
        backdrop = detail.get("backdrop_url") or detail.get("poster_url")
        if backdrop:
            st.markdown(
                textwrap.dedent(f"""
                <div class="hero" style="background-image:url('{backdrop}');">
                  <div class="hero-overlay">
                    <div class="hero-title">{detail['title']}</div>
                    <div class="hero-meta">
                        {"★ " + f"{float(detail['vote_average']):.1f}" if detail.get('vote_average') else ""}
                        &nbsp;·&nbsp; {detail.get('release_year','')}
                        &nbsp;·&nbsp; {detail.get('runtime','?')} min
                        &nbsp;·&nbsp; {detail.get('genres','')}
                        &nbsp;·&nbsp; {detail.get('original_language','').upper()}
                    </div>
                    <div class="hero-overview">{detail.get('overview','')}</div>
                  </div>
                </div>
                """).strip(),
                unsafe_allow_html=True,
            )

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Director:** {detail.get('director') or '—'}")
            st.markdown(f"**Producers:** {detail.get('producers') or '—'}")
            st.markdown(f"**Cast:** {detail.get('cast') or '—'}")
            st.markdown(f"**Genres:** {detail.get('genres') or '—'}")
            st.markdown(f"**Release year:** {detail.get('release_year') or '—'}")
            st.markdown(f"**Runtime:** {detail.get('runtime') or '—'} min")
            st.markdown(f"**Rating:** ★ {detail.get('vote_average') or '—'}")

            rating_info = safe_get(f"{API_URL}/movie/{selected_movie}/rating")
            if rating_info.get("imdb_rating"):
                st.markdown(f"**IMDb rating:** {rating_info['imdb_rating']}/10 ({rating_info.get('imdb_votes','')} votes)")
        with col2:
            if detail.get("watch_link"):
                st.markdown(f"**Where to watch:** {detail.get('watch_platform') or 'See platforms'}")
                st.link_button("▶ Watch / Play", detail["watch_link"])
            else:
                st.caption("No legal streaming link found for this title in your region yet.")

        with st.expander("🔎 More about this movie"):
            web_info = safe_get(f"{API_URL}/movie/{selected_movie}/web")
            if web_info.get("summary"):
                st.write(web_info["summary"])
                if web_info.get("source"):
                    st.caption(f"Source: {web_info['source']}")
            else:
                st.caption("No quick summary found — use the link below to search directly.")
            if web_info.get("search_url"):
                st.link_button("Search the web", web_info["search_url"])

        sim = safe_get(f"{API_URL}/movie/{selected_movie}/similar", params={"k": 12})
        sim_results = sim.get("results", [])
        for r in sim_results:
            r["why"] = shared_genre_reason(detail.get("genres", ""), r.get("genres", ""), r["title"])
        render_hscroll_row("Because you looked at this — and why it's similar", sim_results)

# ============================================================================
# HOME / SEARCH PAGE
# ============================================================================
else:
    st.markdown(f"<div class='app-title'>{APP_NAME}</div>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-sky">
                <span class="star " style="left:44.9%; top:55.3%; width:1.4px; height:1.4px; animation-duration:2.1s; animation-delay:2.0s;"></span>
<span class="star pink" style="left:77.9%; top:10.1%; width:1.7px; height:1.7px; animation-duration:1.6s; animation-delay:3.9s;"></span>
<span class="star " style="left:64.4%; top:60.7%; width:0.9px; height:0.9px; animation-duration:2.1s; animation-delay:1.0s;"></span>
<span class="star " style="left:46.0%; top:43.7%; width:1.4px; height:1.4px; animation-duration:3.5s; animation-delay:1.8s;"></span>
<span class="star blue" style="left:97.8%; top:97.6%; width:1.4px; height:1.4px; animation-duration:2.4s; animation-delay:0.3s;"></span>
<span class="star " style="left:39.8%; top:83.1%; width:1.1px; height:1.1px; animation-duration:2.1s; animation-delay:3.6s;"></span>
<span class="star pink" style="left:96.1%; top:39.6%; width:0.9px; height:0.9px; animation-duration:1.8s; animation-delay:1.3s;"></span>
<span class="star " style="left:74.5%; top:12.4%; width:1.7px; height:1.7px; animation-duration:2.0s; animation-delay:2.2s;"></span>
<span class="star pink" style="left:19.5%; top:72.0%; width:0.9px; height:0.9px; animation-duration:2.1s; animation-delay:1.1s;"></span>
<span class="star pink" style="left:78.9%; top:30.5%; width:1.8px; height:1.8px; animation-duration:3.4s; animation-delay:0.4s;"></span>
<span class="star " style="left:21.7%; top:26.1%; width:1.3px; height:1.3px; animation-duration:1.8s; animation-delay:2.3s;"></span>
<span class="star " style="left:59.3%; top:37.1%; width:1.1px; height:1.1px; animation-duration:4.1s; animation-delay:0.7s;"></span>
<span class="star blue" style="left:89.1%; top:80.3%; width:3.6px; height:3.6px; animation-duration:2.1s; animation-delay:3.8s;"></span>
<span class="star blue" style="left:59.5%; top:41.9%; width:0.9px; height:0.9px; animation-duration:3.6s; animation-delay:1.0s;"></span>
<span class="star " style="left:58.9%; top:29.5%; width:0.9px; height:0.9px; animation-duration:3.2s; animation-delay:3.4s;"></span>
<span class="star " style="left:28.2%; top:90.0%; width:0.9px; height:0.9px; animation-duration:1.7s; animation-delay:0.7s;"></span>
<span class="star " style="left:56.5%; top:13.8%; width:2.4px; height:2.4px; animation-duration:3.6s; animation-delay:2.3s;"></span>
<span class="star blue" style="left:4.4%; top:2.7%; width:1.4px; height:1.4px; animation-duration:3.4s; animation-delay:1.9s;"></span>
<span class="star blue" style="left:31.9%; top:97.9%; width:3.6px; height:3.6px; animation-duration:3.7s; animation-delay:2.8s;"></span>
<span class="star " style="left:89.8%; top:35.1%; width:1.3px; height:1.3px; animation-duration:3.9s; animation-delay:3.5s;"></span>
<span class="star blue" style="left:61.6%; top:38.1%; width:1.2px; height:1.2px; animation-duration:4.5s; animation-delay:3.5s;"></span>
<span class="star " style="left:38.7%; top:72.3%; width:1.2px; height:1.2px; animation-duration:3.8s; animation-delay:0.1s;"></span>
<span class="star " style="left:47.7%; top:23.3%; width:3.5px; height:3.5px; animation-duration:2.3s; animation-delay:0.0s;"></span>
<span class="star " style="left:66.8%; top:20.6%; width:0.9px; height:0.9px; animation-duration:4.2s; animation-delay:1.3s;"></span>
<span class="star " style="left:20.3%; top:42.8%; width:1.4px; height:1.4px; animation-duration:3.2s; animation-delay:1.3s;"></span>
<span class="star " style="left:49.2%; top:82.2%; width:1.4px; height:1.4px; animation-duration:2.0s; animation-delay:1.8s;"></span>
<span class="star " style="left:21.8%; top:41.2%; width:2.0px; height:2.0px; animation-duration:4.4s; animation-delay:1.8s;"></span>
<span class="star " style="left:4.1%; top:85.7%; width:0.8px; height:0.8px; animation-duration:3.9s; animation-delay:0.1s;"></span>
<span class="star " style="left:45.1%; top:3.4%; width:1.4px; height:1.4px; animation-duration:3.4s; animation-delay:1.8s;"></span>
<span class="star " style="left:64.5%; top:79.3%; width:1.5px; height:1.5px; animation-duration:2.0s; animation-delay:0.0s;"></span>
<span class="star " style="left:70.3%; top:18.4%; width:1.0px; height:1.0px; animation-duration:3.3s; animation-delay:3.0s;"></span>
<span class="star blue" style="left:77.8%; top:88.9%; width:0.9px; height:0.9px; animation-duration:2.9s; animation-delay:2.5s;"></span>
<span class="star blue" style="left:37.5%; top:56.2%; width:1.4px; height:1.4px; animation-duration:3.5s; animation-delay:0.8s;"></span>
<span class="star blue" style="left:80.4%; top:63.2%; width:3.9px; height:3.9px; animation-duration:4.4s; animation-delay:2.1s;"></span>
<span class="star " style="left:32.1%; top:89.3%; width:1.4px; height:1.4px; animation-duration:3.2s; animation-delay:3.1s;"></span>
<span class="star " style="left:3.8%; top:79.5%; width:0.8px; height:0.8px; animation-duration:3.9s; animation-delay:0.6s;"></span>
<span class="star " style="left:51.1%; top:71.2%; width:1.4px; height:1.4px; animation-duration:4.3s; animation-delay:0.3s;"></span>
<span class="star " style="left:52.1%; top:29.1%; width:2.2px; height:2.2px; animation-duration:3.2s; animation-delay:1.2s;"></span>
<span class="star " style="left:83.0%; top:88.4%; width:0.9px; height:0.9px; animation-duration:3.2s; animation-delay:0.8s;"></span>
<span class="star " style="left:49.8%; top:59.7%; width:0.8px; height:0.8px; animation-duration:3.9s; animation-delay:2.3s;"></span>
<span class="star " style="left:68.0%; top:7.4%; width:3.9px; height:3.9px; animation-duration:2.3s; animation-delay:1.9s;"></span>
<span class="star " style="left:43.1%; top:80.1%; width:1.4px; height:1.4px; animation-duration:3.4s; animation-delay:3.7s;"></span>
<span class="star " style="left:76.6%; top:3.2%; width:0.9px; height:0.9px; animation-duration:2.6s; animation-delay:2.5s;"></span>
<span class="star " style="left:71.9%; top:12.9%; width:1.2px; height:1.2px; animation-duration:2.8s; animation-delay:1.5s;"></span>
<span class="star blue" style="left:52.3%; top:16.5%; width:0.9px; height:0.9px; animation-duration:4.1s; animation-delay:2.4s;"></span>
<span class="star pink" style="left:23.6%; top:72.9%; width:1.4px; height:1.4px; animation-duration:4.3s; animation-delay:0.9s;"></span>
<span class="star blue" style="left:87.1%; top:14.0%; width:1.0px; height:1.0px; animation-duration:4.0s; animation-delay:1.7s;"></span>
<span class="star " style="left:13.2%; top:40.1%; width:1.6px; height:1.6px; animation-duration:4.2s; animation-delay:3.9s;"></span>
<span class="star " style="left:50.1%; top:74.5%; width:1.2px; height:1.2px; animation-duration:1.8s; animation-delay:0.1s;"></span>
<span class="star " style="left:50.9%; top:56.2%; width:1.8px; height:1.8px; animation-duration:4.5s; animation-delay:3.7s;"></span>
<span class="star " style="left:7.0%; top:93.3%; width:1.1px; height:1.1px; animation-duration:3.0s; animation-delay:1.7s;"></span>
<span class="star " style="left:2.3%; top:69.0%; width:1.8px; height:1.8px; animation-duration:2.7s; animation-delay:0.8s;"></span>
<span class="star " style="left:50.7%; top:2.5%; width:2.3px; height:2.3px; animation-duration:3.4s; animation-delay:1.6s;"></span>
<span class="star " style="left:49.9%; top:96.3%; width:1.8px; height:1.8px; animation-duration:3.8s; animation-delay:3.3s;"></span>
<span class="star " style="left:88.0%; top:86.3%; width:1.3px; height:1.3px; animation-duration:3.7s; animation-delay:0.3s;"></span>
<span class="star " style="left:46.5%; top:2.0%; width:1.0px; height:1.0px; animation-duration:4.3s; animation-delay:2.7s;"></span>
<span class="star pink" style="left:65.0%; top:56.2%; width:1.2px; height:1.2px; animation-duration:3.6s; animation-delay:3.0s;"></span>
<span class="star " style="left:3.2%; top:60.7%; width:1.3px; height:1.3px; animation-duration:2.1s; animation-delay:1.5s;"></span>
<span class="star blue" style="left:25.3%; top:88.8%; width:1.2px; height:1.2px; animation-duration:4.5s; animation-delay:2.6s;"></span>
<span class="star " style="left:8.4%; top:59.0%; width:1.3px; height:1.3px; animation-duration:2.9s; animation-delay:0.7s;"></span>
<span class="star " style="left:60.3%; top:6.7%; width:1.5px; height:1.5px; animation-duration:2.6s; animation-delay:1.1s;"></span>
<span class="star blue" style="left:55.4%; top:28.5%; width:1.3px; height:1.3px; animation-duration:1.6s; animation-delay:0.6s;"></span>
<span class="star " style="left:38.8%; top:88.1%; width:4.0px; height:4.0px; animation-duration:1.7s; animation-delay:3.6s;"></span>
<span class="star blue" style="left:47.3%; top:95.4%; width:2.1px; height:2.1px; animation-duration:2.9s; animation-delay:3.9s;"></span>
<span class="star " style="left:59.6%; top:12.2%; width:1.2px; height:1.2px; animation-duration:3.1s; animation-delay:0.5s;"></span>
<span class="star pink" style="left:65.8%; top:45.2%; width:2.1px; height:2.1px; animation-duration:3.1s; animation-delay:4.0s;"></span>
<span class="star " style="left:72.2%; top:24.1%; width:0.9px; height:0.9px; animation-duration:2.6s; animation-delay:1.1s;"></span>
<span class="star blue" style="left:55.8%; top:58.4%; width:1.2px; height:1.2px; animation-duration:4.4s; animation-delay:3.7s;"></span>
<span class="star " style="left:4.8%; top:6.9%; width:1.0px; height:1.0px; animation-duration:3.1s; animation-delay:0.3s;"></span>
<span class="star blue" style="left:66.6%; top:54.4%; width:1.2px; height:1.2px; animation-duration:2.5s; animation-delay:3.0s;"></span>
<span class="star blue" style="left:8.2%; top:12.6%; width:1.4px; height:1.4px; animation-duration:2.8s; animation-delay:1.0s;"></span>
<span class="star " style="left:36.8%; top:64.4%; width:1.9px; height:1.9px; animation-duration:4.3s; animation-delay:1.7s;"></span>
<span class="star blue" style="left:10.4%; top:85.9%; width:0.9px; height:0.9px; animation-duration:3.6s; animation-delay:1.2s;"></span>
<span class="star " style="left:8.4%; top:21.7%; width:1.7px; height:1.7px; animation-duration:3.6s; animation-delay:1.1s;"></span>
<span class="star blue" style="left:35.7%; top:71.4%; width:1.1px; height:1.1px; animation-duration:4.3s; animation-delay:3.8s;"></span>
<span class="star " style="left:43.5%; top:78.9%; width:3.2px; height:3.2px; animation-duration:4.2s; animation-delay:1.0s;"></span>
<span class="star blue" style="left:36.5%; top:36.2%; width:1.1px; height:1.1px; animation-duration:3.9s; animation-delay:2.2s;"></span>
<span class="star " style="left:55.6%; top:18.1%; width:1.3px; height:1.3px; animation-duration:3.0s; animation-delay:2.2s;"></span>
<span class="star blue" style="left:94.7%; top:64.2%; width:1.7px; height:1.7px; animation-duration:1.8s; animation-delay:0.3s;"></span>
<span class="star blue" style="left:88.2%; top:9.2%; width:1.2px; height:1.2px; animation-duration:2.2s; animation-delay:0.9s;"></span>
<span class="star blue" style="left:51.6%; top:75.2%; width:1.9px; height:1.9px; animation-duration:3.0s; animation-delay:2.1s;"></span>
<span class="star blue" style="left:69.7%; top:89.8%; width:2.3px; height:2.3px; animation-duration:3.9s; animation-delay:3.3s;"></span>
<span class="star blue" style="left:93.9%; top:63.1%; width:1.2px; height:1.2px; animation-duration:2.8s; animation-delay:0.6s;"></span>
<span class="star " style="left:97.1%; top:37.4%; width:0.9px; height:0.9px; animation-duration:4.4s; animation-delay:0.2s;"></span>
<span class="star " style="left:12.1%; top:63.9%; width:1.3px; height:1.3px; animation-duration:3.3s; animation-delay:3.6s;"></span>
<span class="star " style="left:11.5%; top:18.9%; width:1.0px; height:1.0px; animation-duration:2.2s; animation-delay:0.7s;"></span>
<span class="star blue" style="left:17.7%; top:74.5%; width:1.0px; height:1.0px; animation-duration:2.3s; animation-delay:3.5s;"></span>
<span class="star " style="left:34.2%; top:54.1%; width:1.5px; height:1.5px; animation-duration:4.3s; animation-delay:3.2s;"></span>
<span class="star " style="left:52.2%; top:51.0%; width:1.0px; height:1.0px; animation-duration:1.5s; animation-delay:1.9s;"></span>
<span class="star " style="left:78.3%; top:70.2%; width:1.2px; height:1.2px; animation-duration:2.3s; animation-delay:3.5s;"></span>
                <div class="shooting-star" style="left:70%; top:8%; animation-duration:6s; animation-delay:1s;"></div>
                <div class="shooting-star" style="left:30%; top:20%; animation-duration:8s; animation-delay:4s;"></div>
                <div class="shooting-star" style="left:85%; top:50%; animation-duration:7s; animation-delay:2.5s;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.header("🌐 Languages")
        show_languages = st.multiselect(
            "Show rows for:",
            options=[name for _, name in LANGUAGE_ROWS],
            default=[name for _, name in LANGUAGE_ROWS],
        )

        st.header("🎭 Movie Type")
        selected_genres = st.multiselect(
            "Pick one or more types (Action, Comedy, Horror, etc.):",
            options=GENRE_OPTIONS,
            default=[],
        )

        st.header("⚙️ Search options")
        k = st.slider("Number of results", 3, 20, 10)
        explain = st.checkbox("Extra AI explanation (Groq)", value=False)

        with st.expander("🕘 Recent searches (click to show)", expanded=False):
            hist = safe_get(f"{API_URL}/history")
            if isinstance(hist, list) and hist:
                for h in hist[:20]:
                    st.write(f"**{h['query']}**")
                    st.caption(h["top_titles"])
            else:
                st.caption("No searches yet.")

    query = st.text_input(
        "🔍 Describe a plot, mood, or theme",
        placeholder="e.g. a heist that goes wrong told out of order",
        label_visibility="collapsed",
    )
    search_clicked = st.button("🔍 Recommend", type="primary", key="recommend_btn")

    if search_clicked or query:
        if query.strip():
            loading_placeholder = st.empty()
            msg = LOADING_MESSAGES[int(time.time()) % len(LOADING_MESSAGES)]
            loading_placeholder.markdown(
                f"<div class='loading-wrap'><span class='loading-reel'>🎞️</span>"
                f"<span class='loading-text'>{msg}</span></div>",
                unsafe_allow_html=True,
            )
            resp = requests.post(
                f"{API_URL}/recommend",
                json={"query": query, "k": k, "explain": explain},
                timeout=60,
            )
            loading_placeholder.empty()
            try:
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                st.error(f"Couldn't reach backend: {e}")
                data = None

            if data and data["results"]:
                results = [r for r in data["results"] if matches_genres(r, selected_genres)]
                render_hscroll_row(f'Results for "{query}"', results)
            elif data:
                st.warning("No matches found. Try rephrasing your description.")
    else:
        all_movies = safe_get(f"{API_URL}/movies", params={"limit": 400})

        if "__error__" in all_movies:
            st.error(
                f"Couldn't reach the backend server: {all_movies['__error__']}\n\n"
                "Make sure your backend server is running."
            )
        else:
            results = all_movies.get("results", [])
            results = [r for r in results if matches_genres(r, selected_genres)]

            if not results:
                st.info("No movies match your filters yet — try fewer genre filters, or update the catalog for more movies.")
            else:
                if HAS_AUTOREFRESH:
                    tick = st_autorefresh(interval=5000, key="hero_autorefresh")
                else:
                    tick = 0
                manual_offset = st.session_state.get("hero_manual_offset", 0)
                hero_index = (tick + manual_offset) % len(results)
                hero = results[hero_index]
                render_hero(hero, key="hero_next_btn", cyclable=True)

                new_movies = [r for r in results if r.get("is_new")]
                if new_movies:
                    render_hscroll_row("🆕 New & Upcoming", new_movies[:24])

                render_hscroll_row("All Movies", results[:24])

                for code, name in LANGUAGE_ROWS:
                    if name not in show_languages:
                        continue
                    lang_movies = [r for r in results if r.get("original_language") == code]
                    render_hscroll_row(f"{name} Movies", lang_movies[:24])