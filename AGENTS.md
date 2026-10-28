# Working in this repository

Use the repository's [hyb26-skill](.github/skills/hyb26-skill/SKILL.md) for
badge app development, debugging, validation, and deployment. Load that skill
before doing badge work. Its scripts and references are bundled alongside it.

The app lives in `nyan_mona/`, not `badge/apps/nyan_mona/`. Keep this layout
and pass the existing app path to the skill's tools. Run commands from the
repository root:

```bash
python3 .github/skills/hyb26-skill/scripts/validate_app.py ./nyan_mona
```

Use the Universe 2026 runtime, not the 2025 APIs. Follow the skill's deployment
preview, backup, credential, and custom-icon checks. Static validation and the
simulator do not establish that the app works on physical hardware. Report
which checks actually ran and what still needs on-badge verification.
