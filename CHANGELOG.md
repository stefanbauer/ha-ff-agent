# Changelog

## 0.2.1

- Make the bundled card more compact and closer to Mushroom's typography,
  spacing and control sizes without requiring Mushroom to be installed.
- Place the last-reply timestamp on the right, reduce the header/logo and alarm
  banner height, and use shorter horizontal reply buttons.
- Give End local alarm a full-width neutral button below Accept/Reject and
  remove the redundant reply-section caption in English and German.
- Preserve action targeting, alarm/reply behavior and all existing configuration.

## 0.2.0

- Bundle an FF Agent dashboard card with the integration, automatically loaded
  without a separate HACS frontend repository or manual resource setup.
- Show a prominent red active-alarm banner and a calm idle state. Offer Accept
  and Reject as primary replies only during a local active alarm; hide Accept
  after acceptance. Separate End local alarm from real FF-Agent replies.
  Disable buttons while sending, show errors without retries, and target the
  selected organization. Backend actions remain usable independently of alarm activity.
- Always show the last delivered reply and its timestamp. Persist this history
  across new alarms, manual endings and restarts; preserve older recorded replies
  without inventing missing historical timestamps.
- Support English/German, light/dark themes, narrow cards, a native entity/name
  editor and standard Home Assistant card visibility settings.
- Document card setup and upgrades in English and German.

## 0.1.1

- Rename the reply actions to **Accept incident** / **Reject incident** in English
  and **Einsatz zusagen** / **Einsatz absagen** in German. Keep End alarm /
  Einsatz beenden and all action IDs unchanged for existing automations and buttons.
- Allow Accept, Reject and End alarm without an active local or matching FF-Agent
  incident. An HTTP 2xx reply, including “kein passender Einsatz aktiv”, records
  the selected local decision; Reject also ends the local alarm. Preserve state
  on transport/HTTP errors and prevent late replies from changing a newer alarm.
- Classify the displayed webhook host before showing the local-test warning;
  public reverse-proxy URLs no longer receive it merely because HA has no
  configured external URL. Keep warnings for local hostnames and non-public IPs.
- Update the English/German usage and upgrade instructions for version 0.1.1.
- Publish versioned GitHub releases without a `v` prefix and document switching
  existing HACS branch installations to release-based updates.

## 0.1.0

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
