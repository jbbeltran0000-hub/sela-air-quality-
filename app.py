"""Streamlit dashboard for truck-idling hotspot reports."""

from pathlib import Path

import pandas as pd
import streamlit as st

REPORT_PATH = Path("truck_idling_hotspots_report.csv")

st.set_page_config(page_title="Truck Idling Risk Dashboard", layout="wide")
st.title("Truck Idling & Environmental Risk Dashboard")

if not REPORT_PATH.exists():
    st.warning(
        f"No report found at `{REPORT_PATH}`. Run the analyzer script to generate a report."
    )
else:
    try:
        df = pd.read_csv(REPORT_PATH)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as error:
        st.error(f"Could not read the hotspot report: {error}")
    else:
        if df.empty:
            st.info("The hotspot report contains no corridor records.")
        elif "hotspot_score" not in df.columns or "location" not in df.columns:
            st.error("The report must contain `location` and `hotspot_score` columns.")
        else:
            df["hotspot_score"] = pd.to_numeric(df["hotspot_score"], errors="coerce")
            df = df.dropna(subset=["hotspot_score"]).sort_values(
                "hotspot_score", ascending=False
            )

            if df.empty:
                st.info("The report contains no valid hotspot scores.")
            else:
                st.subheader("Latest Corridor Risk Rankings")
                st.dataframe(df, use_container_width=True, hide_index=True)

                top_spot = df.iloc[0]
                st.error(
                    f"⚠️ Highest Priority Corridor: **{top_spot['location']}** "
                    f"(Score: {top_spot['hotspot_score']})"
                )

                if "time_period" in df.columns:
                    period = df.iloc[0]["time_period"]
                    if pd.notna(period):
                        st.caption(f"Report time period: {str(period).replace('_', ' ').title()}")
