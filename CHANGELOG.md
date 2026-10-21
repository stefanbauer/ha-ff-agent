# Changelog

## Unreleased

- Classify the displayed webhook host before showing the local-test warning;
  public reverse-proxy URLs no longer receive it merely because HA has no
  configured external URL. Keep warnings for local hostnames and non-public IPs.
- Add per-organization alarm activity and reply-status entities, grouped under
  their own FF-Agent device, with English/German names and states.
- End local alarms after four hours without extending the deadline for repeated
  hooks; preserve the deadline and reply across Home Assistant restarts.
- Add targeted Accept, Reject and End alarm actions. Acceptance explicitly sends
  the configured transport and HA home coordinates; rejection sends neither.
  Successful rejection also ends the local alarm and retains the rejected status;
  failed or unconfirmed rejection leaves it active. Ending an alarm manually is
  local only and retains its last reply.
- Keep reply status unchanged on failed/unconfirmed requests or no active incident,
  never follow redirects or retry automatically, and prevent late replies from
  overwriting a newer alarm.
- Add multiple named FF Agent services with a UI configuration flow, editable
  reply UUID (no full URLs) and default transport (CAR/BICYCLE/FEET).
- Generate a persistent secret GET-only alarm webhook per service, emitting a local
  `ff_agent_alarm` event with its config entry ID; no incident payload processing.
- Show the configured external HTTPS webhook URL, or a full local test URL with
  a warning about public reachability and Home Assistant Cloud by Nabu Casa.
- Acknowledge GET reception in plain text without caching; reject POST and avoid
  triggering alarms for HEAD requests. Warn that opening or previewing the URL triggers it.
- Add the supplied FF-Agent symbol without lettering, preserving the complete
  image and its proportions, and set development version 0.1.0.
- Provide English UI text and German translations.
- Provide English and German end-user instructions with language links in README;
  move Docker, development and reset instructions to dev/README.md.
- Add official My Home Assistant buttons for opening/adding the HACS repository
  and starting integration setup, with public custom-repository installation and
  backup guidance for controlled production testing; no default-catalog submission.
- License code and original documentation under MIT, excluding the FF-Agent logo
  and name; add English/German third-party rights and independence notices.
- Add official hassfest and HACS validation jobs alongside the pinned runtime tests.
- Enable native My Home Assistant redirects in the minimal local test instance.
- Initial Home Assistant custom-integration scaffold for FF Agent, without
  provider functionality or a dashboard card.
- Isolated local Home Assistant 2026.10.2 environment with a direct source mount,
  persistent test data, containerized Python checks and GitHub CI.
