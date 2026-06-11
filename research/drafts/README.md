# Research Drafts

`scripts/research_pipeline.py` writes candidate JSON files here when run locally or from the manual GitHub Action.

Draft files are review artifacts, not production data. After review, selected fields should be promoted into `public/data/companies/*.json`, followed by:

```bash
python3 scripts/build_company_index.py
python3 scripts/validate_data.py
npm run sync:pages
```

Generated `*.draft.json` files are ignored by git by default.
