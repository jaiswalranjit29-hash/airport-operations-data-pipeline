# Airport Operations Management Summary

## Executive overview

The pipeline processed **800** records. **728** records were accepted and **72** were rejected, resulting in an acceptance rate of **91.00%**.

Operationally, the valid records show an on-time rate of **49.45%**, a delay rate of **46.29%**, and a cancellation rate of **4.26%**. Average delay was **22.99 minutes**, while the 90th percentile was **53.00 minutes**.

## Main findings

- **Airline requiring attention:** Condor had the highest delay rate at **52.50%** across 80 flights.
- **Route requiring attention:** FRA-HAM had the highest delay rate at **55.77%**, with an average delay of **23.92 minutes**.
- **Passenger volume:** The accepted records represent **136,120 passengers**.
- **Data quality:** The most frequent quality rule was **DQ001 - missing flight_id**, with 8 issues.

## Recommended actions

1. Review operational causes behind the highest-delay airline and route, especially flights in the `61-120` and `120+` delay bands.
2. Assign owners to all open high-severity quality issues and track them through resolution.
3. Track rejection rate and open-issue age as recurring management KPIs.
4. Refresh the Power BI dashboard after each pipeline run and investigate material month-over-month changes.

## Important limitation

The included data is synthetic and is intended to demonstrate the technical and analytical workflow. Operational conclusions should not be interpreted as real airline performance.
