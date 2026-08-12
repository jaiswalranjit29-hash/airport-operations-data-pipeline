let
    Source = Csv.Document(
        File.Contents(ProjectRoot & "\data\powerbi\fact_quality_issues.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders,{
        {"issue_id", type text}, {"source_row_number", Int64.Type}, {"flight_id", type text},
        {"rule_code", type text}, {"quality_dimension", type text}, {"severity", type text},
        {"issue_description", type text}, {"workflow_status", type text}, {"owner", type text},
        {"resolution_notes", type text}
    })
in
    TypedColumns
