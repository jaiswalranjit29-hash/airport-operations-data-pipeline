# DAX Measures

The report uses the following measures in `FactFlights` and `FactQualityIssues`.

```DAX
Total Flights = COUNTROWS(FactFlights)
```

```DAX
Total Passengers = SUM(FactFlights[passengers])
```

```DAX
On-Time Flights =
CALCULATE([Total Flights], FactFlights[is_on_time] = TRUE())
```

```DAX
Delayed Flights =
CALCULATE([Total Flights], FactFlights[is_delayed] = TRUE())
```

```DAX
Cancelled Flights =
CALCULATE([Total Flights], FactFlights[is_cancelled] = TRUE())
```

```DAX
On-Time Rate = DIVIDE([On-Time Flights], [Total Flights])
```

```DAX
Delay Rate = DIVIDE([Delayed Flights], [Total Flights])
```

```DAX
Cancellation Rate = DIVIDE([Cancelled Flights], [Total Flights])
```

```DAX
Average Delay Minutes = AVERAGE(FactFlights[delay_minutes])
```

```DAX
P90 Delay Minutes =
PERCENTILEX.INC(FactFlights, FactFlights[delay_minutes], 0.9)
```

```DAX
Total Quality Issues = COUNTROWS(FactQualityIssues)
```

```DAX
Open Quality Issues =
CALCULATE(
    [Total Quality Issues],
    FactQualityIssues[workflow_status] = "Open"
)
```

```DAX
Open High-Severity Issues =
CALCULATE(
    [Total Quality Issues],
    FactQualityIssues[workflow_status] = "Open",
    FactQualityIssues[severity] = "High"
)
```

Format the rate measures as percentages with two decimal places.
