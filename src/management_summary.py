"""Create a concise management-facing Markdown summary from pipeline reports."""
from __future__ import annotations

import pandas as pd


def create_management_summary(reports: dict[str, pd.DataFrame]) -> str:
    """Build a readable Markdown summary while handling empty operational results."""
    executive = reports["executive"].iloc[0]

    if reports["airline"].empty:
        airline_sentence = (
            "No airline performance ranking is available because no valid flights "
            "were accepted."
        )
    else:
        top_airline = reports["airline"].iloc[0]
        airline_sentence = (
            f"{top_airline['airline']} had the highest delay rate at "
            f"**{top_airline['delay_rate_pct']:.2f}%** across "
            f"{int(top_airline['total_flights'])} flights."
        )

    if reports["route"].empty:
        route_sentence = (
            "No route performance ranking is available because no valid flights "
            "were accepted."
        )
    else:
        top_route = reports["route"].iloc[0]
        route_sentence = (
            f"{top_route['route']} had the highest delay rate at "
            f"**{top_route['delay_rate_pct']:.2f}%**, with an average delay of "
            f"**{top_route['average_delay_minutes']:.2f} minutes**."
        )

    if reports["quality"].empty:
        quality_sentence = "No data-quality issues were detected."
    else:
        top_quality = reports["quality"].iloc[0]
        quality_sentence = (
            f"The most frequent quality rule was **{top_quality['rule_code']} - "
            f"{top_quality['issue_description']}**, with "
            f"{int(top_quality['issue_count'])} issues."
        )

    overview = (
        f"The pipeline processed **{int(executive['extracted_records']):,}** records. "
        f"**{int(executive['accepted_records']):,}** records were accepted and "
        f"**{int(executive['rejected_records']):,}** were rejected, resulting in an "
        f"acceptance rate of **{executive['acceptance_rate_pct']:.2f}%**."
    )
    operations = (
        "Operationally, the valid records show an on-time rate of "
        f"**{executive['on_time_rate_pct']:.2f}%**, a delay rate of "
        f"**{executive['delay_rate_pct']:.2f}%**, and a cancellation rate of "
        f"**{executive['cancellation_rate_pct']:.2f}%**. Average delay was "
        f"**{executive['average_delay_minutes']:.2f} minutes**, while the 90th "
        f"percentile was **{executive['p90_delay_minutes']:.2f} minutes**."
    )

    lines = [
        "# Airport Operations Management Summary",
        "",
        "## Executive overview",
        "",
        overview,
        "",
        operations,
        "",
        "## Main findings",
        "",
        f"- **Airline requiring attention:** {airline_sentence}",
        f"- **Route requiring attention:** {route_sentence}",
        (
            "- **Passenger volume:** The accepted records represent "
            f"**{int(executive['total_passengers']):,} passengers**."
        ),
        f"- **Data quality:** {quality_sentence}",
        "",
        "## Recommended actions",
        "",
        (
            "1. Review operational causes behind the highest-delay airline and route, "
            "especially flights in the `61-120` and `120+` delay bands."
        ),
        (
            "2. Assign owners to all open high-severity quality issues and track them "
            "through resolution."
        ),
        "3. Track rejection rate and open-issue age as recurring management KPIs.",
        (
            "4. Refresh the Power BI dashboard after each pipeline run and investigate "
            "material month-over-month changes."
        ),
        "",
        "## Important limitation",
        "",
        (
            "The included data is synthetic and is intended to demonstrate the technical "
            "and analytical workflow. Operational conclusions should not be interpreted "
            "as real airline performance."
        ),
        "",
    ]
    return "\n".join(lines)
