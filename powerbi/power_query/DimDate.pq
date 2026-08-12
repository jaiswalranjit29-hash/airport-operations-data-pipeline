let
    Source = Csv.Document(
        File.Contents(ProjectRoot & "\data\powerbi\dim_date.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders,{
        {"date_key", Int64.Type}, {"date", type date}, {"year", Int64.Type},
        {"quarter", type text}, {"month_number", Int64.Type}, {"month_name", type text},
        {"week_number", Int64.Type}, {"weekday_number", Int64.Type}, {"weekday_name", type text}
    })
in
    TypedColumns
