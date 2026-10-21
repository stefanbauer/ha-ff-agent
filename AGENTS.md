# FF Agent for Home Assistant

- Work in this repository, normally directly on `main`. Do not change the sibling
  Gladys repositories. No extra worktrees or threads unless explicitly requested.
- This is a development scaffold, not a working FF-Agent integration. Do not add
  provider functionality, configuration flows, entities or a dashboard card as
  incidental setup work.
- All installable integration files belong in `custom_components/ff_agent`.
  Preserve the domain `ff_agent`. Follow official Home Assistant and HACS patterns.
- Never commit credentials, personal reply UUIDs, real incident payloads, Home
  Assistant tokens, runtime databases or `.storage` files. Tests must not contact
  FF Agent or send real accept/reject requests.
- Use the pinned Home Assistant container and Ruff service in `compose.yaml`.
  See README for lint, formatting, smoke tests and configuration validation.
- Source is bind-mounted read-only into local Home Assistant; restart the service
  after Python changes. Runtime state lives in the project-specific Docker volume.
- Full reset is destructive to this test instance. Do not execute it against an
  existing user's state without explicit approval. Never use global Docker prune.
- Keep user-visible changes in `CHANGELOG.md`. Publishing, releases, tags and
  changing repository visibility require explicit authorization.
