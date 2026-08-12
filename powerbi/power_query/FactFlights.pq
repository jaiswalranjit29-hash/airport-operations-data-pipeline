let
    Source = Csv.Document(
        File.Contents(ProjectRoot & "\data\powerbi\fact_flights.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders,{
        {"flight_key", Int64.Type}, {"flight_id", type text}, {"airline_key", Int64.Type},
        {"origin_airport_key", Int64.Type}, {"destination_airport_key", Int64.Type},
        {"date_key", Int64.Type}, {"scheduled_time", type datetime}, {"actual_time", type datetime},
        {"scheduled_hour", Int64.Type}, {"route", type text}, {"gate", type text},
        {"status", type text}, {"passengers", Int64.Type}, {"delay_minutes", Int64.Type},
        {"delay_band", type text}, {"is_on_time", type logical}, {"is_delayed", type logical},
        {"is_cancelled", type logical}
    }),
    RemovedDuplicateFlights = Table.Distinct(TypedColumns, {"flight_id"})
in
    RemovedDuplicateFlights
