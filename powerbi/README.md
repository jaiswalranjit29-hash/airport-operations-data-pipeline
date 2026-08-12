# Power BI Assets

The Python pipeline exports Power BI-ready CSV files to `data/powerbi/`.

## Included files

- `model_guide.md` — relationships and recommended report layout.
- `dax_measures.md` — measures for operational and quality KPIs.
- `power_query/` — Power Query scripts for loading generated CSV files.

## Rebuilding the report

1. Run `python -m src.main` from the repository root.
2. Open Power BI Desktop and create a text parameter named `ProjectRoot` that points to the local repository root.
3. Create the Power Query queries from `power_query/*.pq` and import the dimensions described in `model_guide.md`.
4. Create the relationships from `model_guide.md`.
5. Add the measures from `dax_measures.md`.
6. Build report pages from the generated facts, dimensions, and KPI measures.

## Public-repository note

The original development `.pbix` is not included because its binary metadata contained environment-specific service/connection information. A rebuilt PBIX using only local project sources can be added after its data-source metadata has been reviewed.
