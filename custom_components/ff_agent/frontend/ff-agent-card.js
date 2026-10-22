/* FF Agent's bundled dashboard card. No external scripts, fonts or requests. */
const TEXT = {
  en: {
    active: "Incident active",
    idle: "No active incident",
    unavailable: "Alarm status unavailable",
    accepted: "Accepted",
    rejected: "Rejected",
    accept: "Accept",
    reject: "Reject",
    end_alarm: "End local alarm",
    acceptLabel: "Accept incident",
    rejectLabel: "Reject incident",
    end_alarmLabel: "End local alarm without sending a reply",
    history: "Last reply",
    noReply: "No reply sent yet",
    unknownTime: "Time not recorded",
    replyUnavailable: "Reply status unavailable",
    sending: "Sending…",
    ending: "Ending…",
    error:
      "The action could not be completed. Check FF-Agent before trying again.",
  },
  de: {
    active: "Einsatz aktiv",
    idle: "Kein aktiver Einsatz",
    unavailable: "Einsatzstatus nicht verfügbar",
    accepted: "Zugesagt",
    rejected: "Abgesagt",
    accept: "Zusagen",
    reject: "Absagen",
    end_alarm: "Einsatz lokal beenden",
    acceptLabel: "Einsatz zusagen",
    rejectLabel: "Einsatz absagen",
    end_alarmLabel: "Einsatz lokal beenden, ohne Rückmeldung zu senden",
    history: "Letzte Rückmeldung",
    noReply: "Noch keine Rückmeldung gesendet",
    unknownTime: "Zeitpunkt nicht erfasst",
    replyUnavailable: "Rückmeldestatus nicht verfügbar",
    sending: "Wird gesendet…",
    ending: "Wird beendet…",
    error:
      "Die Aktion konnte nicht abgeschlossen werden. Prüfe FF-Agent vor einem erneuten Versuch.",
  },
};

const ICONS = {
  alarm:
    '<path d="M5 19h14M8 16v-5a4 4 0 0 1 8 0v5ZM12 2v2M3 6l2 2M21 6l-2 2M2 13h2M20 13h2"/>',
  idle: '<path d="m12 3 8 3v6c0 4-5 7-8 9-3-2-8-5-8-9V6ZM8 12l3 3 5-6"/>',
  unavailable: '<circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 17h.01"/>',
  accept: '<path d="m5 12 4 4L19 6"/>',
  reject: '<path d="m6 6 12 12M6 18 18 6"/>',
  end_alarm: '<rect x="6" y="6" width="12" height="12" rx="2"/>',
};
const svg = (name) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;

class FFAgentCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; --ff-red: #b91c28; --ff-green: #166534; }
        * { box-sizing: border-box; }
        [hidden] { display: none !important; }
        ha-card {
          display: block; overflow: hidden;
          background: var(--ha-card-background, var(--card-background-color, #fff));
          color: var(--primary-text-color, #202124);
          border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, #dfe3e8);
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, none);
          font-family: var(--ha-font-family-body, var(--paper-font-body1_-_font-family, Roboto, sans-serif));
        }
        header { display: flex; align-items: center; gap: 10px; padding: 10px 12px; }
        header img { width: 24px; height: 28px; object-fit: contain; flex-shrink: 0; }
        .identity { min-width: 0; flex: 1; }
        h2 { font-size: var(--mush-card-primary-font-size, 14px); font-weight: var(--mush-card-primary-font-weight, 500); line-height: 20px; margin: 0; overflow-wrap: anywhere; }
        .signal { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: var(--secondary-background-color, #f3f5f7); }
        #signal-icon { display: flex; flex-shrink: 0; }
        .signal svg { width: 24px; height: 24px; }
        .signal h3 { font-size: 14px; font-weight: 500; line-height: 20px; margin: 0; }
        ha-card[data-active] .signal { background: var(--ff-red); color: #fff; }
        ha-card[data-active] .signal h3 { font-size: 20px; line-height: 24px; font-weight: 600; }
        .actions { padding: 12px; }
        .reply-actions { display: flex; gap: 8px; }
        .reply-actions button { flex: 1; min-width: 0; }
        button { min-height: var(--mush-control-height, 42px); padding: 8px 12px; border-radius: var(--mush-control-border-radius, 12px); border: 1px solid var(--divider-color, #dfe3e8); background: transparent; color: inherit; font: inherit; font-size: 13px; font-weight: 500; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 7px; }
        button svg { width: 20px; height: 20px; flex-shrink: 0; }
        button[data-action="accept"] { background: var(--ff-green); border-color: var(--ff-green); color: #fff; }
        button[data-action="reject"] { color: var(--error-color, #b91c28); border-color: currentColor; }
        button.local-action { width: 100%; margin-top: 8px; background: var(--secondary-background-color, #f3f5f7); }
        button.local-action svg { width: 18px; height: 18px; }
        button:hover:not(:disabled) { filter: brightness(.92); }
        button:focus-visible { outline: 3px solid var(--primary-color, #03a9f4); outline-offset: 3px; }
        button:disabled { cursor: wait; opacity: .55; }
        footer { display: flex; gap: 10px; align-items: center; padding: 10px 12px; border-top: 1px solid var(--divider-color, #e4e7eb); }
        .history-icon { width: 28px; height: 28px; display: grid; place-items: center; border-radius: 50%; background: var(--secondary-background-color, #f3f5f7); color: var(--secondary-text-color, #616873); flex-shrink: 0; }
        .history-icon svg { width: 16px; height: 16px; }
        .history-copy { min-width: 0; flex: 1; }
        .caption { color: var(--secondary-text-color, #616873); font-size: 11px; font-weight: 500; }
        .decision { margin-top: 2px; font-size: 14px; font-weight: 500; line-height: 20px; }
        time { display: block; max-width: 45%; text-align: end; font-size: 11px; line-height: 16px; color: var(--secondary-text-color, #616873); overflow-wrap: anywhere; font-variant-numeric: tabular-nums; }
        .empty { font-size: 12px; font-weight: 400; color: var(--secondary-text-color, #616873); line-height: 16px; }
        .error { margin: 0 12px 12px; padding: 10px; border: 1px solid var(--error-color, #b91c28); border-radius: 8px; color: var(--error-color, #b91c28); font-size: 12px; line-height: 1.5; overflow-wrap: anywhere; }
      </style>
      <ha-card>
        <header><img src="/ff_agent/icon.png" alt=""><div class="identity"><h2 id="name"></h2></div></header>
        <section class="signal" role="status" aria-live="polite">
          <span id="signal-icon">${svg("idle")}</span>
          <h3 id="status"></h3>
        </section>
        <div class="actions" id="actions" hidden>
          <div class="reply-actions">
            ${["accept", "reject"].map((action) => `<button type="button" data-action="${action}">${svg(action)}<span></span></button>`).join("")}
          </div>
          <button type="button" class="local-action" data-action="end_alarm">${svg("end_alarm")}<span></span></button>
        </div>
        <p class="error" id="error" role="alert" hidden></p>
        <footer>
          <span class="history-icon" id="history-icon">${svg("accept")}</span>
          <div class="history-copy"><div class="caption" id="history-label"></div><div class="decision" id="decision"></div></div>
          <time id="time"></time>
        </footer>
      </ha-card>`;
    for (const button of this.shadowRoot.querySelectorAll("button")) {
      button.addEventListener("click", () =>
        this._perform(button.dataset.action),
      );
    }
  }

  setConfig(config) {
    if (!config.entity?.startsWith("binary_sensor.")) {
      throw new Error(
        "FF Agent: choose an Alarm active binary sensor (entity).",
      );
    }
    this._config = { ...config };
    this._error = "";
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _t(key) {
    return TEXT[this._hass?.language?.startsWith("de") ? "de" : "en"][key];
  }

  _text(id, value) {
    const node = this.shadowRoot.getElementById(id);
    if (node.textContent !== value) node.textContent = value;
  }

  _alarmEntry() {
    const entry = this._hass?.entities?.[this._config?.entity];
    return entry?.platform === "ff_agent" &&
      entry.translation_key === "alarm_active"
      ? entry
      : undefined;
  }

  _replyState() {
    const device = this._alarmEntry()?.device_id;
    if (!device) return undefined;
    const entry = Object.values(this._hass.entities).find(
      (item) =>
        item.device_id === device &&
        item.platform === "ff_agent" &&
        item.translation_key === "reply_status",
    );
    return this._hass.states[entry?.entity_id];
  }

  _active() {
    return (
      Boolean(this._alarmEntry()) &&
      this._hass?.states[this._config?.entity]?.state === "on"
    );
  }

  _render() {
    if (!this._hass || !this._config) return;
    const alarm = this._hass.states[this._config.entity];
    const reply = this._replyState();
    const device = this._hass.devices?.[this._alarmEntry()?.device_id];
    const active = this._active();
    const available =
      Boolean(this._alarmEntry()) && ["on", "off"].includes(alarm?.state);
    const card = this.shadowRoot.querySelector("ha-card");
    card.toggleAttribute("data-active", active);
    card.setAttribute("aria-busy", String(Boolean(this._busy)));
    this._text(
      "name",
      this._config.name ||
        device?.name_by_user ||
        device?.name ||
        alarm?.attributes.friendly_name ||
        "FF Agent",
    );
    this._text(
      "status",
      this._t(!available ? "unavailable" : active ? "active" : "idle"),
    );
    this.shadowRoot.getElementById("signal-icon").innerHTML = svg(
      !available ? "unavailable" : active ? "alarm" : "idle",
    );
    this.shadowRoot.getElementById("actions").hidden = !active;
    for (const button of this.shadowRoot.querySelectorAll("button")) {
      const action = button.dataset.action;
      button.hidden = action === "accept" && reply?.state === "accepted";
      button.disabled = !active || Boolean(this._busy) || button.hidden;
      button.setAttribute("aria-label", this._t(`${action}Label`));
      button.querySelector("span").textContent = this._t(
        this._busy === action
          ? action === "end_alarm"
            ? "ending"
            : "sending"
          : action,
      );
    }
    this._text("history-label", this._t("history"));
    const last = reply?.attributes.last_reply_status;
    const hasReply = ["accepted", "rejected"].includes(last);
    const replyAvailable =
      reply && !["unknown", "unavailable"].includes(reply.state);
    this._text(
      "decision",
      hasReply
        ? this._t(last)
        : this._t(replyAvailable ? "noReply" : "replyUnavailable"),
    );
    this.shadowRoot
      .getElementById("decision")
      .classList.toggle("empty", !hasReply);
    this.shadowRoot.getElementById("history-icon").innerHTML = svg(
      last === "rejected" ? "reject" : "accept",
    );
    const at = reply?.attributes.last_reply_at;
    const date = at ? new Date(at) : null;
    const time = this.shadowRoot.getElementById("time");
    time.hidden = !hasReply;
    time.removeAttribute("datetime");
    if (date && !Number.isNaN(date.valueOf())) {
      time.dateTime = date.toISOString();
      this._text(
        "time",
        new Intl.DateTimeFormat(
          this._hass.locale?.language || this._hass.language || "en",
          {
            dateStyle: "medium",
            timeStyle: "short",
            timeZone: this._hass.config.time_zone,
          },
        ).format(date),
      );
    } else {
      this._text("time", this._t("unknownTime"));
    }
    this._text("error", this._error || "");
    this.shadowRoot.getElementById("error").hidden = !this._error;
  }

  async _perform(action) {
    if (!this._active() || this._busy) return;
    this._busy = action;
    this._error = "";
    this._render();
    try {
      await this._hass.callService(
        "ff_agent",
        action,
        {},
        { entity_id: this._config.entity },
      );
    } catch (error) {
      this._error = error?.message || this._t("error");
    } finally {
      this._busy = null;
      this._render();
    }
  }

  getCardSize() {
    return this._active() ? 6 : 3;
  }
  getGridOptions() {
    return { columns: 12, rows: "auto", min_columns: 6 };
  }

  static getStubConfig(hass, entities = [], entitiesFallback = []) {
    const entries = hass.entities || {};
    const ordered = [...entities, ...entitiesFallback, ...Object.keys(entries)];
    const entity = ordered.find(
      (id) =>
        entries[id]?.platform === "ff_agent" &&
        entries[id].translation_key === "alarm_active" &&
        id.startsWith("binary_sensor."),
    );
    return { type: "custom:ff-agent-card", ...(entity ? { entity } : {}) };
  }

  static getConfigForm() {
    return {
      schema: [
        {
          name: "entity",
          required: true,
          selector: {
            entity: {
              filter: { domain: "binary_sensor", integration: "ff_agent" },
            },
          },
        },
        { name: "name", selector: { text: {} } },
      ],
      computeLabel: (schema, localize) =>
        localize(`ui.panel.lovelace.editor.card.generic.${schema.name}`),
    };
  }
}

if (!customElements.get("ff-agent-card")) {
  customElements.define("ff-agent-card", FFAgentCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "ff-agent-card",
    name: "FF Agent",
    description: "Alarm status and replies · Einsatzstatus und Rückmeldung",
    preview: true,
  });
}
