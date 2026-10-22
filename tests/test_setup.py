"""Exercise FF Agent against the pinned Home Assistant, without provider calls."""

import asyncio
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import httpx
from aiohttp import ClientSession
from aiohttp.test_utils import make_mocked_request
from homeassistant import loader
from homeassistant.auth import auth_manager_from_config
from homeassistant.bootstrap import async_load_base_functionality
from homeassistant.components import webhook
from homeassistant.components.http import current_request
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.config_entries import ConfigEntries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.setup import async_setup_component
from homeassistant.util.aiohttp import MockRequest
from voluptuous import Invalid
from yarl import URL

REPLY_A = "00000000-0000-4000-8000-000000000001"
REPLY_B = "12345678-9abc-4def-8123-000000000002"


class SetupTest(unittest.IsolatedAsyncioTestCase):
    """Use disposable HA state, never the developer's accounts or config entries."""

    async def asyncSetUp(self) -> None:
        """Initialize the real HA dependencies and mounted integration."""
        self.config_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.config_dir.cleanup)
        Path(self.config_dir.name, "custom_components").symlink_to(
            "/config/custom_components", target_is_directory=True
        )
        self.hass = HomeAssistant(self.config_dir.name)
        self.addAsyncCleanup(self.hass.async_stop)
        loader.async_setup(self.hass)
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.assertTrue(await async_load_base_functionality(self.hass))
        self.hass.auth = await auth_manager_from_config(
            self.hass, [{"type": "homeassistant"}], []
        )
        self.assertTrue(
            await async_setup_component(
                self.hass,
                "ff_agent",
                {"http": {"server_host": "127.0.0.1", "server_port": 18123}},
            )
        )
        await self.hass.async_start()
        self.hass.config.internal_url = "http://127.0.0.1:18123"
        self.provider_handler = None
        self.provider_requests = []

        def provider(request):
            self.provider_requests.append(request)
            if self.provider_handler is None:
                raise AssertionError("Unexpected outbound request")
            return self.provider_handler(request)

        client = httpx.AsyncClient(transport=httpx.MockTransport(provider))
        self.addAsyncCleanup(client.aclose)
        client_patch = patch(
            "custom_components.ff_agent.coordinator.get_async_client",
            return_value=client,
        )
        client_patch.start()
        self.addCleanup(client_patch.stop)

    async def test_scaffold_loads_without_entities_or_actions(self) -> None:
        """Loading alone does not create entities or reply actions."""
        self.assertIn("ff_agent", self.hass.config.components)
        self.assertEqual(self.hass.states.async_entity_ids("ff_agent"), [])
        self.assertNotIn("ff_agent", self.hass.services.async_services())
        # Discover the module even when the original HTML had no extra import.
        resources = self.hass.data[LOVELACE_DATA].resources
        await resources.async_get_info()
        integration = await loader.async_get_integration(self.hass, "ff_agent")
        self.assertEqual(
            [(item["type"], item["url"]) for item in resources.async_items()],
            [("module", f"/ff_agent/ff-agent-card.js?v={integration.version}")],
        )
        async with ClientSession() as client:
            with patch(
                "homeassistant.components.frontend.onboarding.async_is_onboarded",
                return_value=True,
            ):
                async with client.get("http://127.0.0.1:18123/") as response:
                    self.assertIn(
                        "/ff_agent/ff-agent-card.js?v=", await response.text()
                    )
            async with client.get(
                "http://127.0.0.1:18123/ff_agent/ff-agent-card.js"
            ) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("ff-agent-card", await response.text())

    async def add_service(self, name, reply_id, transport):
        """Complete the same flow used by the native frontend."""
        flow = await self.hass.config_entries.flow.async_init(
            "ff_agent", context={"source": "user"}
        )
        self.assertEqual(flow["step_id"], "user")
        self.assertEqual(
            flow["data_schema"]({"name": name, "reply_id": reply_id})["transport"],
            "car",
        )
        flow = await self.hass.config_entries.flow.async_configure(
            flow["flow_id"],
            flow["data_schema"](
                {"name": name, "reply_id": reply_id, "transport": transport.lower()}
            ),
        )
        self.assertEqual(flow["step_id"], "webhook_local")
        shown_url = flow["description_placeholders"]["webhook_url"]
        result = await self.hass.config_entries.flow.async_configure(
            flow["flow_id"], {}
        )
        self.assertEqual(result["type"], "create_entry")
        await self.hass.async_block_till_done()
        return result["result"], shown_url

    def entity_ids(self, entry):
        """Discover each organization's registered public entities."""
        return {
            entity.domain: entity.entity_id
            for entity in er.async_entries_for_config_entry(
                er.async_get(self.hass), entry.entry_id
            )
        }

    async def alarm(self, entry):
        """Deliver an incoming hook without reaching the provider."""
        await webhook.async_handle_webhook(
            self.hass, entry.data["webhook_id"], MockRequest(b"", "test", method="GET")
        )
        await self.hass.async_block_till_done()

    async def action(self, name, entry):
        """Use the same targeted service API as automations and future cards."""
        await self.hass.services.async_call(
            "ff_agent",
            name,
            {"entity_id": self.entity_ids(entry)["binary_sensor"]},
            blocking=True,
        )
        await self.hass.async_block_till_done()

    async def test_alarm_expiry_reload_and_manual_end(self) -> None:
        """Bound each alarm across reloads; manual end cannot send a reply."""
        first, _ = await self.add_service("First", REPLY_A, "CAR")
        second, _ = await self.add_service("Second", REPLY_B, "FEET")
        ids = self.entity_ids(first)
        self.assertEqual(set(ids), {"binary_sensor", "sensor"})
        self.assertEqual(self.hass.states.get(ids["binary_sensor"]).state, "off")
        self.assertEqual(self.hass.states.get(ids["sensor"]).state, "pending")
        start = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)
        deadline = start + timedelta(hours=4)
        scheduled = []

        def schedule(hass, action, point):
            timer = (point, action)
            scheduled.append(timer)
            return lambda: scheduled.remove(timer)

        with (
            patch("custom_components.ff_agent.coordinator.dt_util.utcnow") as now,
            patch(
                "custom_components.ff_agent.coordinator.async_track_point_in_utc_time",
                side_effect=schedule,
            ),
        ):
            now.return_value = start
            await self.alarm(first)
            self.assertEqual(self.hass.states.get(ids["binary_sensor"]).state, "on")
            self.assertEqual(
                self.hass.states.get(ids["binary_sensor"]).attributes["expires_at"],
                deadline,
            )
            self.assertEqual(
                self.hass.states.get(self.entity_ids(second)["binary_sensor"]).state,
                "off",
            )
            now.return_value = deadline - timedelta(seconds=1)
            await self.alarm(first)
            self.assertTrue(await self.hass.config_entries.async_reload(first.entry_id))
            await self.hass.async_block_till_done()
            state = self.hass.states.get(ids["binary_sensor"])
            self.assertEqual(state.state, "on")
            self.assertEqual(state.attributes["expires_at"], deadline)
            now.return_value = deadline
            for point, expire in list(scheduled):
                if point <= deadline:
                    expire(deadline)
            await self.hass.async_block_till_done()
            self.assertEqual(self.hass.states.get(ids["binary_sensor"]).state, "off")
            await self.alarm(first)
            device_id = (
                er.async_get(self.hass).async_get(ids["binary_sensor"]).device_id
            )
            self.assertIsNotNone(device_id)
            await self.hass.services.async_call(
                "ff_agent", "end_alarm", {"device_id": device_id}, blocking=True
            )
            await self.hass.async_block_till_done()
            self.assertEqual(self.hass.states.get(ids["binary_sensor"]).state, "off")
            self.assertEqual(self.provider_requests, [])
            await self.alarm(first)
            self.assertTrue(await self.hass.config_entries.async_unload(first.entry_id))
            now.return_value += timedelta(hours=4, seconds=1)
            self.assertTrue(await self.hass.config_entries.async_setup(first.entry_id))
            await self.hass.async_block_till_done()
            self.assertEqual(self.hass.states.get(ids["binary_sensor"]).state, "off")

    async def test_reply_actions_and_failures(self) -> None:
        """Send exact requests; preserve status on errors and never follow redirects."""
        first, _ = await self.add_service("First", REPLY_A, "BICYCLE")
        second, _ = await self.add_service("Second", REPLY_B, "FEET")
        ids = self.entity_ids(first)
        self.hass.config.latitude = 48.125
        self.hass.config.longitude = -11.875
        self.assertEqual(self.provider_requests, [])
        self.provider_handler = lambda request: httpx.Response(200, text="OK")
        await self.alarm(first)
        with self.assertRaises(Invalid):
            await self.hass.services.async_call("ff_agent", "accept", {}, blocking=True)
        self.assertEqual(self.provider_requests, [])
        await self.action("accept", first)
        request = self.provider_requests[-1]
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url.host, "www.ff-agent.com")
        self.assertEqual(request.url.path, f"/app2/missionreplies/{REPLY_A}/accept")
        self.assertEqual(
            dict(request.url.params),
            {"transport": "BICYCLE", "lat": "48.125", "lng": "-11.875"},
        )
        self.assertEqual(self.hass.states.get(ids["sensor"]).state, "accepted")
        await self.alarm(first)
        self.assertEqual(self.hass.states.get(ids["sensor"]).state, "accepted")
        self.assertTrue(await self.hass.config_entries.async_reload(first.entry_id))
        await self.hass.async_block_till_done()
        self.assertEqual(self.hass.states.get(ids["sensor"]).state, "accepted")
        await self.action("reject", first)
        request = self.provider_requests[-1]
        self.assertEqual(
            str(request.url),
            f"https://www.ff-agent.com/app2/missionreplies/{REPLY_A}/reject",
        )
        self.assertEqual(self.hass.states.get(ids["sensor"]).state, "rejected")
        self.assertEqual(self.hass.states.get(ids["binary_sensor"]).state, "off")
        self.assertIsNone(
            self.hass.states.get(ids["binary_sensor"]).attributes["expires_at"]
        )
        self.assertTrue(await self.hass.config_entries.async_reload(first.entry_id))
        await self.hass.async_block_till_done()
        self.assertEqual(self.hass.states.get(ids["binary_sensor"]).state, "off")
        self.assertEqual(self.hass.states.get(ids["sensor"]).state, "rejected")
        self.assertEqual(len(self.provider_requests), 2)
        await self.alarm(first)
        self.assertEqual(self.hass.states.get(ids["sensor"]).state, "pending")
        for response in (
            httpx.Response(
                302, headers={"Location": "https://example.org/must-not-follow"}
            ),
            httpx.Response(
                500, text="Cannot update status of Person. Internal Error - Check URL!"
            ),
        ):
            with self.subTest(status=response.status_code):
                self.provider_handler = lambda request, response=response: response
                before = len(self.provider_requests)
                with self.assertRaises(HomeAssistantError):
                    await self.action("reject", first)
                self.assertEqual(len(self.provider_requests), before + 1)
                self.assertEqual(self.hass.states.get(ids["sensor"]).state, "pending")
                self.assertEqual(self.hass.states.get(ids["binary_sensor"]).state, "on")

        def timeout(request):
            raise httpx.ReadTimeout("Unconfirmed", request=request)

        self.provider_handler = timeout
        before = len(self.provider_requests)
        with self.assertRaises(HomeAssistantError) as raised:
            await self.action("reject", first)
        self.assertNotIn(REPLY_A, str(raised.exception))
        self.assertEqual(len(self.provider_requests), before + 1)
        self.assertEqual(self.hass.states.get(ids["sensor"]).state, "pending")
        self.assertEqual(self.hass.states.get(ids["binary_sensor"]).state, "on")
        self.assertEqual(
            self.hass.states.get(self.entity_ids(second)["sensor"]).state, "pending"
        )

    async def test_actions_without_active_incident(self) -> None:
        """Actions work without a local alarm or a matching provider incident."""
        first, _ = await self.add_service("First", REPLY_A, "CAR")
        second, _ = await self.add_service("Second", REPLY_B, "FEET")
        await self.alarm(second)
        ids = self.entity_ids(first)
        self.provider_handler = lambda request: httpx.Response(
            200, text=" Updated MissionStatus: kein passender Einsatz aktiv\n"
        )
        device_id = er.async_get(self.hass).async_get(ids["binary_sensor"]).device_id
        for active in (False, True):
            with self.subTest(local_alarm_active=active):
                if active:
                    await self.alarm(first)
                await self.action("accept", first)
                self.assertEqual(self.hass.states.get(ids["sensor"]).state, "accepted")
                self.assertEqual(
                    self.hass.states.get(ids["binary_sensor"]).state,
                    "on" if active else "off",
                )
                await self.hass.services.async_call(
                    "ff_agent", "reject", {"device_id": device_id}, blocking=True
                )
                await self.hass.async_block_till_done()
                self.assertEqual(
                    self.hass.states.get(ids["binary_sensor"]).state, "off"
                )
                self.assertIsNone(
                    self.hass.states.get(ids["binary_sensor"]).attributes["expires_at"]
                )
                self.assertEqual(self.hass.states.get(ids["sensor"]).state, "rejected")
                await self.action("end_alarm", first)
                self.assertEqual(
                    self.hass.states.get(ids["binary_sensor"]).state, "off"
                )
                self.assertEqual(self.hass.states.get(ids["sensor"]).state, "rejected")
                self.assertEqual(
                    self.hass.states.get(
                        self.entity_ids(second)["binary_sensor"]
                    ).state,
                    "on",
                )
        self.assertTrue(await self.hass.config_entries.async_reload(first.entry_id))
        await self.hass.async_block_till_done()
        self.assertEqual(self.hass.states.get(ids["binary_sensor"]).state, "off")
        self.assertEqual(self.hass.states.get(ids["sensor"]).state, "rejected")
        self.assertEqual(len(self.provider_requests), 4)

    async def test_last_reply_history_survives_new_alarm_and_reload(self) -> None:
        """Keep a real reply timestamp, never an alarm/reset/failure timestamp."""
        entry, _ = await self.add_service("History", REPLY_A, "CAR")
        sensor = self.entity_ids(entry)["sensor"]
        self.assertIsNone(self.hass.states.get(sensor).attributes["last_reply_at"])
        self.provider_handler = lambda request: httpx.Response(200, text="OK")
        accepted_at = datetime(2026, 10, 22, 9, 42, tzinfo=UTC)
        with patch(
            "custom_components.ff_agent.coordinator.dt_util.utcnow",
            return_value=accepted_at,
        ):
            await self.action("accept", entry)
        await self.alarm(entry)
        state = self.hass.states.get(sensor)
        self.assertEqual(state.state, "pending")
        self.assertEqual(state.attributes["last_reply_status"], "accepted")
        self.assertEqual(state.attributes["last_reply_at"], accepted_at)
        self.provider_handler = lambda request: httpx.Response(503)
        with self.assertRaises(HomeAssistantError):
            await self.action("reject", entry)
        await self.action("end_alarm", entry)
        self.assertTrue(await self.hass.config_entries.async_reload(entry.entry_id))
        await self.hass.async_block_till_done()
        state = self.hass.states.get(sensor)
        self.assertEqual(state.attributes["last_reply_status"], "accepted")
        self.assertEqual(state.attributes["last_reply_at"], accepted_at)
        self.provider_handler = lambda request: httpx.Response(200, text="OK")
        rejected_at = accepted_at + timedelta(minutes=7)
        with patch(
            "custom_components.ff_agent.coordinator.dt_util.utcnow",
            return_value=rejected_at,
        ):
            await self.action("reject", entry)
        self.assertTrue(await self.hass.config_entries.async_reload(entry.entry_id))
        await self.hass.async_block_till_done()
        state = self.hass.states.get(sensor)
        self.assertEqual(state.attributes["last_reply_status"], "rejected")
        self.assertEqual(state.attributes["last_reply_at"], rejected_at)

        # Upgrade old persisted state without inventing a historical timestamp.
        self.assertTrue(await self.hass.config_entries.async_unload(entry.entry_id))
        await Store(self.hass, 1, f"ff_agent.{entry.entry_id}").async_save(
            {"reply_status": "accepted", "expires_at": None}
        )
        self.assertTrue(await self.hass.config_entries.async_setup(entry.entry_id))
        await self.hass.async_block_till_done()
        state = self.hass.states.get(sensor)
        self.assertEqual(state.attributes["last_reply_status"], "accepted")
        self.assertIsNone(state.attributes["last_reply_at"])

    async def test_inflight_reply_does_not_overwrite_a_new_alarm(self) -> None:
        """A late HTTP response must not resolve a newer local alarm."""
        entry, _ = await self.add_service("Race", REPLY_A, "CAR")
        for decision, body in (
            ("accept", "OK"),
            ("reject", "Updated MissionStatus: kein passender Einsatz aktiv"),
        ):
            with self.subTest(decision=decision):
                await self.alarm(entry)
                started = asyncio.Event()
                finish = asyncio.Event()

                async def delayed(request, started=started, finish=finish, body=body):
                    started.set()
                    await finish.wait()
                    return httpx.Response(200, text=body)

                self.provider_handler = delayed
                reply = asyncio.create_task(self.action(decision, entry))
                await started.wait()
                await self.hass.services.async_call(
                    "ff_agent",
                    "end_alarm",
                    {"entity_id": self.entity_ids(entry)["binary_sensor"]},
                    blocking=True,
                )
                await webhook.async_handle_webhook(
                    self.hass,
                    entry.data["webhook_id"],
                    MockRequest(b"", "test", method="GET"),
                )
                finish.set()
                with self.assertRaises(HomeAssistantError):
                    await reply
                self.assertEqual(
                    self.hass.states.get(self.entity_ids(entry)["sensor"]).state,
                    "pending",
                )
                self.assertIsNone(
                    self.hass.states.get(self.entity_ids(entry)["sensor"]).attributes[
                        "last_reply_at"
                    ]
                )
                self.assertEqual(
                    self.hass.states.get(self.entity_ids(entry)["binary_sensor"]).state,
                    "on",
                )

    async def test_independent_services_webhooks_and_reconfiguration(self) -> None:
        """Route alarms separately; retain a secret across edits and reloads."""
        first, first_url = await self.add_service(
            " Feuerwehr Berglern ", f" {REPLY_A} ", "BICYCLE"
        )
        second, second_url = await self.add_service(
            "Other organization", REPLY_B.upper(), "FEET"
        )
        self.assertEqual(first.title, "Feuerwehr Berglern")
        self.assertEqual(first.data["reply_id"], REPLY_A)
        self.assertEqual(first.data["transport"], "BICYCLE")
        self.assertEqual(second.data["reply_id"], REPLY_B)
        self.assertEqual(second.data["transport"], "FEET")
        self.assertNotEqual(first_url, second_url)
        self.assertEqual(
            first_url, f"http://127.0.0.1:18123/api/webhook/{first.data['webhook_id']}"
        )

        events = []
        self.hass.bus.async_listen("ff_agent_alarm", events.append)
        async with ClientSession() as client:
            for url in (first_url, second_url):
                async with client.get(url) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(
                        await response.text(), "Alarm signal received by FF Agent."
                    )
                    self.assertEqual(response.headers["Cache-Control"], "no-store")
            for method, status in (("POST", 405), ("HEAD", 200)):
                async with client.request(method, first_url) as response:
                    self.assertEqual(response.status, status)
        await self.hass.async_block_till_done()
        self.assertEqual(
            [event.data for event in events],
            [{"config_entry_id": first.entry_id}, {"config_entry_id": second.entry_id}],
        )
        self.hass.config.external_url = "https://ha.example.org"
        options = await self.hass.config_entries.options.async_init(first.entry_id)
        self.assertEqual(options["step_id"], "init")
        self.assertEqual(
            options["description_placeholders"]["webhook_url"],
            f"https://ha.example.org/api/webhook/{first.data['webhook_id']}",
        )
        await self.hass.config_entries.options.async_configure(options["flow_id"], {})
        flow = await self.hass.config_entries.flow.async_init(
            "ff_agent",
            context={"source": "reconfigure", "entry_id": first.entry_id},
        )
        self.assertEqual(
            flow["data_schema"]({"name": first.title, "reply_id": REPLY_A})[
                "transport"
            ],
            "bicycle",
        )
        result = await self.hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {"name": "Renamed organization", "reply_id": REPLY_A, "transport": "car"},
        )
        self.assertEqual(result["reason"], "reconfigure_successful")
        await self.hass.async_block_till_done()
        self.assertEqual(first.title, "Renamed organization")
        self.assertEqual(first.data["transport"], "CAR")
        self.assertEqual(
            f"http://127.0.0.1:18123/api/webhook/{first.data['webhook_id']}", first_url
        )
        response = await webhook.async_handle_webhook(
            self.hass,
            first.data["webhook_id"],
            MockRequest(b"", "test", method="GET"),
        )
        self.assertEqual(response.status, 200)
        await self.hass.async_block_till_done()
        self.assertEqual(len(events), 3)

        self.assertTrue(await self.hass.config_entries.async_unload(first.entry_id))
        await webhook.async_handle_webhook(
            self.hass, first.data["webhook_id"], MockRequest(b"", "test", method="GET")
        )
        await webhook.async_handle_webhook(
            self.hass,
            second.data["webhook_id"],
            MockRequest(b"", "test", method="GET"),
        )
        await self.hass.async_block_till_done()
        self.assertEqual(len(events), 4)
        self.assertEqual(events[-1].data, {"config_entry_id": second.entry_id})

    async def test_webhook_url_preserves_browser_port(self) -> None:
        """Show the browser's mapped port and warn only without external HTTPS."""
        token = current_request.set(
            make_mocked_request("POST", "/", headers={"Host": "localhost:8124"})
        )
        try:
            entry, url = await self.add_service("Local test", REPLY_A, "CAR")
            self.assertEqual(
                url, f"http://localhost:8124/api/webhook/{entry.data['webhook_id']}"
            )
            options = await self.hass.config_entries.options.async_init(entry.entry_id)
            self.assertEqual(options["step_id"], "local")
            self.assertEqual(options["description_placeholders"]["webhook_url"], url)
            await self.hass.config_entries.options.async_configure(
                options["flow_id"], {}
            )
            self.hass.config.external_url = "https://alarms.example.org"
            options = await self.hass.config_entries.options.async_init(entry.entry_id)
            self.assertEqual(options["step_id"], "init")
            self.assertEqual(
                options["description_placeholders"]["webhook_url"],
                f"https://alarms.example.org/api/webhook/{entry.data['webhook_id']}",
            )
        finally:
            current_request.reset(token)

    async def test_webhook_warning_matches_displayed_host(self) -> None:
        """Warn about local hosts, not missing external-URL configuration."""
        entry, _ = await self.add_service("URL classification", REPLY_A, "CAR")
        for base, local in (
            ("https://ha.example.org", False),
            ("https://ha.example.org:8443", False),
            ("https://8.8.8.8", False),
            ("http://localhost:8124", True),
            ("https://ha.localhost", True),
            ("http://127.0.0.1:8124", True),
            ("https://192.168.12.34", True),
            ("http://10.23.45.67:8123", True),
            ("https://172.20.1.2", True),
            ("http://[::1]:8123", True),
            ("https://[fd12:3456::1]", True),
            ("https://ha.local", True),
            ("https://ha.lan", True),
            ("https://ha.home.arpa", True),
            ("https://homeassistant", True),
        ):
            with self.subTest(base=base):
                token = current_request.set(
                    make_mocked_request("POST", base + "/").clone(
                        scheme=URL(base).scheme
                    )
                )
                try:
                    options = await self.hass.config_entries.options.async_init(
                        entry.entry_id
                    )
                    self.assertEqual(options["step_id"], "local" if local else "init")
                    self.assertEqual(
                        options["description_placeholders"]["webhook_url"],
                        f"{base}/api/webhook/{entry.data['webhook_id']}",
                    )
                    await self.hass.config_entries.options.async_configure(
                        options["flow_id"], {}
                    )
                finally:
                    current_request.reset(token)

        token = current_request.set(
            make_mocked_request("POST", "https://ha.example.org/").clone(scheme="https")
        )
        try:
            flow = await self.hass.config_entries.flow.async_init(
                "ff_agent", context={"source": "user"}
            )
            result = await self.hass.config_entries.flow.async_configure(
                flow["flow_id"],
                {"name": "External", "reply_id": REPLY_B, "transport": "car"},
            )
            self.assertEqual(result["step_id"], "webhook")
            self.hass.config_entries.flow.async_abort(flow["flow_id"])
        finally:
            current_request.reset(token)

        for base, local in (
            ("https://ha.local", True),
            ("https://alarms.example.org", False),
        ):
            with self.subTest(configured_external=base):
                self.hass.config.external_url = base
                options = await self.hass.config_entries.options.async_init(
                    entry.entry_id
                )
                self.assertEqual(options["step_id"], "local" if local else "init")
                self.assertEqual(
                    options["description_placeholders"]["webhook_url"],
                    f"{base}/api/webhook/{entry.data['webhook_id']}",
                )
                await self.hass.config_entries.options.async_configure(
                    options["flow_id"], {}
                )

    async def test_invalid_and_duplicate_reply_settings(self) -> None:
        """Reject complete URLs and duplicate IDs instead of extracting UUIDs."""
        await self.add_service("Existing", REPLY_A, "CAR")
        flow = await self.hass.config_entries.flow.async_init(
            "ff_agent", context={"source": "user"}
        )
        for invalid in (
            "not-a-uuid",
            f"https://www.ff-agent.com/app2/missionreplies/{REPLY_B}/accept?transport=CAR",
            f"https://www.ff-agent.com/app2/missionreplies/{REPLY_B}/reject",
            REPLY_B.replace("-", ""),
            f"urn:uuid:{REPLY_B}",
        ):
            with self.subTest(invalid=invalid):
                result = await self.hass.config_entries.flow.async_configure(
                    flow["flow_id"],
                    {"name": "New", "reply_id": invalid, "transport": "car"},
                )
                self.assertEqual(result["errors"], {"reply_id": "invalid_reply_id"})
        result = await self.hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {"name": "Duplicate", "reply_id": REPLY_A, "transport": "car"},
        )
        self.assertEqual(result["errors"], {"reply_id": "already_configured"})
        result = await self.hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {"name": "  ", "reply_id": REPLY_B, "transport": "car"},
        )
        self.assertEqual(result["errors"], {"name": "name_required"})
        pending = await self.hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {"name": "Pending", "reply_id": REPLY_B, "transport": "car"},
        )
        self.assertEqual(pending["step_id"], "webhook_local")
        await self.add_service("Added in another dialog", REPLY_B, "FEET")
        result = await self.hass.config_entries.flow.async_configure(
            flow["flow_id"], {}
        )
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "already_configured")
        self.assertEqual(len(self.hass.config_entries.async_entries("ff_agent")), 2)
