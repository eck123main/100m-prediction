"""
Web app for the 100m model.

    py -3.14 -m streamlit run app.py
"""

import os

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from backtest import get_real_finals, run_backtest
from features import ATHLETE_ALIASES, RACE_KEYS, compute_all_time_stats, compute_stats_before, load_clean_data
from predict import predict_race_full

BLUE = "#2a78d6"
ORANGE = "#eb6834"

st.set_page_config(page_title="100m Predictor", page_icon="🏃", layout="wide")


@st.cache_resource(show_spinner="Loading race data...")
def get_data():
    return load_clean_data()


@st.cache_data(show_spinner="Running backtest on every real final (about 10 seconds)...")
def get_backtest():
    np.random.seed(0)
    return run_backtest(get_data())


@st.cache_data
def stats_as_of(cutoff):
    df = get_data()
    if cutoff is None:
        return compute_all_time_stats(df)
    return compute_stats_before(pd.Timestamp(cutoff), df)


def clean_name(name):
    name = name.strip().title()
    return ATHLETE_ALIASES.get(name, name)


def prob_chart(probs):
    data = probs.rename("win_prob").rename_axis("athlete").reset_index()
    return alt.Chart(data).mark_bar(color=BLUE, cornerRadiusEnd=4, height=18).encode(
        x=alt.X("win_prob:Q", title="Win probability", axis=alt.Axis(format=".0%", tickCount=5, grid=True)),
        y=alt.Y("athlete:N", sort="-x", title=None),
        tooltip=[alt.Tooltip("athlete:N", title="Athlete"),
                 alt.Tooltip("win_prob:Q", title="Win probability", format=".1%")],
    ).properties(height=max(160, 34 * len(data)))


def prediction_table(probs, stats):
    table = stats.loc[probs.index, ["weighted_avg_time", "finish_rate", "races_used", "elo"]].copy()
    table.insert(0, "win_prob", probs)
    table.columns = ["Win prob", "Form time (s)", "Finish rate", "Races", "Elo"]
    return table.style.format({"Win prob": "{:.1%}", "Form time (s)": "{:.2f}",
                               "Finish rate": "{:.0%}", "Races": "{:.0f}", "Elo": "{:.0f}"})


df = get_data()
latest = df["date"].max()

st.title("Men's 100m Predictor")
st.caption(f"Win probabilities from {len(df):,} World Athletics results, through {latest:%d %b %Y}. "
           "Form is wind- and round-adjusted, weighted toward recent races, combined with a "
           "head-to-head Elo rating.")

predict_tab, replay_tab, record_tab = st.tabs(["Predict a race", "Replay a past final", "Track record"])

# ---------------------------------------------------------------- Predict
with predict_tab:
    all_stats = stats_as_of(None)
    recent = df[df["date"] >= latest - pd.Timedelta(days=365)]["ATHLETE"].unique()
    active = all_stats.loc[all_stats.index.intersection(recent)].dropna(subset=["weighted_avg_time"])
    default_field = active.sort_values("weighted_avg_time").index[:8].tolist()

    with st.expander("Load the field from a World Athletics page"):
        url = st.text_input("Race or meeting URL",
                            placeholder="https://worldathletics.org/competition/calendar-results/results/...")
        if st.button("Fetch start list") and url:
            from scraper import fetch_start_list
            try:
                fetched = [clean_name(n) for n in fetch_start_list(url)]
                st.session_state["field"] = [n for n in fetched if n in all_stats.index]
                missing = [n for n in fetched if n not in all_stats.index]
                st.success(f"Found {len(fetched)} athletes.")
                if missing:
                    st.info(f"No race history for: {', '.join(missing)}")
            except Exception as e:
                st.error(f"Couldn't read a start list from that page: {e}")

    field = st.multiselect(
        "Athletes in the race",
        options=sorted(all_stats.index),
        default=st.session_state.get("field", default_field),
        help="Defaults to the 8 fastest athletes on current form who raced in the last year.",
    )

    if len(field) < 2:
        st.info("Pick at least two athletes.")
    else:
        np.random.seed(0)
        probs = predict_race_full(field, all_stats)
        left, right = st.columns([3, 2])
        with left:
            st.altair_chart(prob_chart(probs), width="stretch")
        with right:
            fav = probs.index[0]
            st.metric("Favourite", fav)
            st.markdown(f"**{probs.iloc[0]:.0%}** chance to win")
            st.caption("Sprint finals are decided by hundredths: treat these as odds, not a verdict.")
        st.dataframe(prediction_table(probs, all_stats), width="stretch")

# ---------------------------------------------------------------- Replay
with replay_tab:
    finals = get_real_finals(df)
    races = (finals.groupby(RACE_KEYS)
             .agg(date=("date", "first"), meet=("meet_name", "first"), n=("ATHLETE", "size"))
             .reset_index().dropna(subset=["date"]).sort_values("date", ascending=False))
    races["label"] = races["date"].dt.strftime("%Y-%m-%d") + " — " + races["meet"].fillna("?").str.slice(0, 60)
    choice = st.selectbox("Final", races["label"], index=0)
    race_row = races[races["label"] == choice].iloc[0]
    race = finals[(finals["source_url"] == race_row["source_url"]) & (finals["heat"] == race_row["heat"])]

    stats = stats_as_of(race_row["date"].date())
    np.random.seed(0)
    probs = predict_race_full(race["ATHLETE"].tolist(), stats)
    result = race[["ATHLETE", "time", "record_flag", "wind"]].sort_values("time", na_position="last")
    result["record_flag"] = result["record_flag"].where(result["record_flag"].notna(), "")
    result.insert(0, "Place", range(1, len(result) + 1))
    result["Model win prob"] = result["ATHLETE"].map(probs).fillna(0.0)
    result["Model rank"] = result["ATHLETE"].map({a: i + 1 for i, a in enumerate(probs.index)})
    winner = result.dropna(subset=["time"]).iloc[0]["ATHLETE"] if result["time"].notna().any() else None

    st.caption("Prediction uses only results from before the race date — exactly what the model "
               "would have said beforehand.")
    if winner is not None and len(probs):
        hit = probs.index[0] == winner
        c1, c2, c3 = st.columns(3)
        c1.metric("Winner", winner)
        c2.metric("Model's pick", probs.index[0], "correct" if hit else "missed",
                  delta_color="normal" if hit else "inverse")
        c3.metric("Probability given to winner", f"{probs.get(winner, 0):.0%}")
    left, right = st.columns([3, 2])
    with left:
        if len(probs):
            st.altair_chart(prob_chart(probs), width="stretch")
    with right:
        st.dataframe(
            result.rename(columns={"ATHLETE": "Athlete", "time": "Time", "record_flag": "Note", "wind": "Wind"})
            .style.format({"Model win prob": "{:.1%}", "Time": "{:.2f}", "Wind": "{:+.1f}",
                           "Model rank": "{:.0f}"}, na_rep="—"),
            hide_index=True, width="stretch",
        )
    no_history = [a for a in race["ATHLETE"] if a not in probs.index]
    if no_history:
        st.caption(f"No earlier results for: {', '.join(no_history)}")

# ---------------------------------------------------------------- Track record
with record_tab:
    results = get_backtest()
    warm = results[results["winner_had_history"]]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Finals tested", f"{len(results)}")
    c2.metric("Picked the winner", f"{results['blend10_correct'].mean():.0%}")
    c3.metric("Fastest-time rule", f"{results['baseline_correct'].mean():.0%}")
    c4.metric("Random guess", f"{results['chance_accuracy'].mean():.0%}")
    st.caption(f"Leak-free: each final is predicted using only earlier results. Excluding the "
               f"{len(results) - len(warm)} finals won by an athlete with no earlier races: "
               f"{warm['blend10_correct'].mean():.0%}.")

    left, right = st.columns(2)
    with left:
        st.subheader("Calibration")
        st.caption("When the model gives its pick X%, how often does that athlete win?")
        r = results.copy()
        r["bucket"] = pd.cut(r["top_pick_prob"], [0, .3, .4, .5, .6, 1],
                             labels=["<30%", "30–40%", "40–50%", "50–60%", "60%+"])
        cal = r.groupby("bucket", observed=True).agg(
            predicted=("top_pick_prob", "mean"), actual=("mc_correct", "mean"), races=("mc_correct", "size"),
        ).reset_index()
        long = cal.melt(id_vars=["bucket", "races"], value_vars=["predicted", "actual"],
                        var_name="series", value_name="rate")
        long["series"] = long["series"].map({"predicted": "Model said", "actual": "Actually won"})
        chart = alt.Chart(long).mark_bar(cornerRadiusEnd=4).encode(
            x=alt.X("bucket:N", title="Model's probability for its pick", sort=None,
                    axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("series:N", sort=["Model said", "Actually won"]),
            y=alt.Y("rate:Q", title=None, axis=alt.Axis(format="%")),
            color=alt.Color("series:N", scale=alt.Scale(domain=["Model said", "Actually won"],
                                                        range=[BLUE, ORANGE]),
                            legend=alt.Legend(title=None, orient="top")),
            tooltip=[alt.Tooltip("bucket:N", title="Bucket"), alt.Tooltip("series:N", title=""),
                     alt.Tooltip("rate:Q", format=".0%", title="Rate"), alt.Tooltip("races:Q", title="Races")],
        ).properties(height=280)
        st.altair_chart(chart, width="stretch")
    with right:
        st.subheader("Accuracy by year")
        st.caption("Share of finals where the model's pick won.")
        by_year = (results.assign(year=results["date"].dt.year)
                   .groupby("year").agg(accuracy=("blend10_correct", "mean"), races=("blend10_correct", "size"))
                   .reset_index())
        by_year = by_year[by_year["year"] >= 2012]
        chart = alt.Chart(by_year).mark_bar(color=BLUE, cornerRadiusEnd=4).encode(
            x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("accuracy:Q", title=None, axis=alt.Axis(format="%")),
            tooltip=[alt.Tooltip("year:O", title="Year"), alt.Tooltip("accuracy:Q", format=".0%", title="Accuracy"),
                     alt.Tooltip("races:Q", title="Finals")],
        ).properties(height=280)
        st.altair_chart(chart, width="stretch")

    st.subheader("Live predictions")
    if os.path.exists("predictions_log.csv"):
        log = pd.read_csv("predictions_log.csv")
        st.caption("Logged before the race with `predict.py --log`; grade them with `score_predictions.py`.")
        st.dataframe(log, hide_index=True, width="stretch")
    else:
        st.caption("None yet. Log predictions before real races with "
                   "`py -3.14 predict.py --startlist <url> --log` and they'll show up here.")

    with st.expander("Every backtested final"):
        show = results[["date", "actual_winner", "top_pick", "top_pick_prob", "prob_assigned_to_winner",
                        "field_size", "blend10_correct"]].sort_values("date", ascending=False)
        show.columns = ["Date", "Winner", "Model's pick", "Pick prob", "Prob to winner", "Field", "Correct"]
        st.dataframe(show.style.format({"Pick prob": "{:.0%}", "Prob to winner": "{:.0%}",
                                        "Date": lambda d: f"{d:%Y-%m-%d}"}),
                     hide_index=True, width="stretch")
