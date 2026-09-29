"""Config flow for Centsys Gate Remote (OTP onboarding)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CentsysRemoteClient, to_international_number
from .api.exceptions import CentsysError, OtpInvalidError
from .const import (
    CONF_COUNTRY,
    CONF_EMAIL,
    CONF_ENABLE_LIVE_LISTENER,
    CONF_MOBILE_NUMBER,
    CONF_NAME,
    CONF_OTP_PLATFORM,
    CONF_REGION,
    CONF_TOKEN,
    DEFAULT_OTP_PLATFORM,
    DOMAIN,
    OTP_PLATFORM_SMS,
    OTP_PLATFORM_WHATSAPP,
)
from .countries import COUNTRIES, DEFAULT_COUNTRY, region_for_country

_DIAL_CODES = {iso: dial for iso, _name, dial in COUNTRIES}

_COUNTRY_OPTIONS = [
    selector.SelectOptionDict(value=iso, label=f"{name} (+{dial})")
    for iso, name, dial in COUNTRIES
]

# Datacentre override. "auto" derives the region from the chosen country (the
# usual case); the two explicit values cover the rare number-vs-gate mismatch.
REGION_AUTO = "auto"
_REGION_OPTIONS = [
    selector.SelectOptionDict(value=REGION_AUTO, label="Auto (from country)"),
    selector.SelectOptionDict(value="za", label="South Africa"),
    selector.SelectOptionDict(value="au", label="Australia & New Zealand"),
]


def _resolve_region(country: str, override: str | None) -> str:
    """Turn the country + optional override into a stored region ("za"/"au")."""
    if override and override != REGION_AUTO:
        return override
    return region_for_country(country)


def _account_schema(
    *,
    country: str = DEFAULT_COUNTRY,
    number: str = "",
    region_override: str = REGION_AUTO,
    otp_platform: int = DEFAULT_OTP_PLATFORM,
    include_contact: bool = True,
) -> vol.Schema:
    """Build the account form. Shared by initial setup and reconfigure."""
    fields: dict[Any, Any] = {
        vol.Required(CONF_COUNTRY, default=country): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=_COUNTRY_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(CONF_MOBILE_NUMBER, default=number): str,
    }
    if include_contact:
        fields[vol.Optional(CONF_NAME)] = str
        fields[vol.Optional(CONF_EMAIL)] = str
    fields[vol.Required(CONF_REGION, default=region_override)] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=_REGION_OPTIONS,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )
    fields[vol.Required(CONF_OTP_PLATFORM, default=str(otp_platform))] = vol.In(
        {
            str(OTP_PLATFORM_WHATSAPP): "WhatsApp",
            str(OTP_PLATFORM_SMS): "SMS",
        }
    )
    return vol.Schema(fields)

OTP_SCHEMA = vol.Schema({vol.Required("otp"): str})


class CentsysConfigFlow(ConfigFlow, domain=DOMAIN):
    """Two-step flow: collect number -> send OTP, then verify OTP -> store token.

    Reauthentication reuses the same OTP exchange, skipping the number step
    because the entry already knows the number and delivery channel.
    """

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "CentsysOptionsFlow":
        return CentsysOptionsFlow(config_entry)

    def __init__(self) -> None:
        self._client: CentsysRemoteClient | None = None
        self._number: str | None = None
        self._name: str | None = None
        self._email: str | None = None
        self._country: str = DEFAULT_COUNTRY
        self._region: str = region_for_country(DEFAULT_COUNTRY)
        self._otp_platform: int = DEFAULT_OTP_PLATFORM
        self._reauth_entry: ConfigEntry | None = None
        self._reconfigure_entry: ConfigEntry | None = None
        self._otp_sent = False

    async def _async_send_otp(self) -> str | None:
        """Start an OTP exchange for ``self._number`` on the account's region.

        Returns an error key for the form, or None once the PIN is on its way.
        """
        if not self._number:
            return "cannot_connect"
        self._client = CentsysRemoteClient(
            self._number,
            session=async_get_clientsession(self.hass),
            region=self._region,
        )
        try:
            sent = await self._client.send_otp(otp_platform=self._otp_platform)
        except CentsysError:
            return "cannot_connect"
        return None if sent else "otp_not_sent"

    async def _async_validate_otp(self, otp: str) -> tuple[str | None, str | None]:
        """Exchange an OTP for a session token. Returns (token, error key)."""
        if self._client is None:
            return None, "cannot_connect"
        try:
            return await self._client.validate_otp(otp.strip()), None
        except OtpInvalidError:
            return None, "invalid_otp"
        except CentsysError:
            return None, "cannot_connect"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._country = user_input[CONF_COUNTRY]
            self._number = to_international_number(
                user_input[CONF_MOBILE_NUMBER], _DIAL_CODES[self._country]
            )
            self._name = user_input.get(CONF_NAME)
            self._email = user_input.get(CONF_EMAIL)
            self._region = _resolve_region(self._country, user_input.get(CONF_REGION))
            self._otp_platform = int(
                user_input.get(CONF_OTP_PLATFORM, DEFAULT_OTP_PLATFORM)
            )

            if not self._number.lstrip("+").isdigit() or len(self._number) < 8:
                errors["base"] = "invalid_number"
            else:
                await self.async_set_unique_id(self._number)
                self._abort_if_unique_id_configured()

                error = await self._async_send_otp()
                if error is None:
                    return await self.async_step_otp()
                errors["base"] = error

        return self.async_show_form(
            step_id="user", data_schema=_account_schema(), errors=errors
        )

    async def async_step_otp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            token, error = await self._async_validate_otp(user_input["otp"])
            if error:
                errors["base"] = error
            else:
                # We create the entry even if no gates are linked yet: the
                # coordinator re-checks on every poll and gates appear
                # automatically once the number is added as a remote user. A
                # repair issue (see coordinator) explains the empty state in
                # the meantime.
                return self.async_create_entry(
                    title=self._name or self._number or "Centsys Gate",
                    data={
                        CONF_MOBILE_NUMBER: self._number,
                        CONF_TOKEN: token,
                        CONF_NAME: self._name,
                        CONF_EMAIL: self._email,
                        CONF_COUNTRY: self._country,
                        CONF_REGION: self._region,
                        CONF_OTP_PLATFORM: self._otp_platform,
                    },
                )

        return self.async_show_form(
            step_id="otp", data_schema=OTP_SCHEMA, errors=errors
        )

    # -- reauthentication --------------------------------------------------

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle a rejected session token by signing in again."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        self._number = entry_data[CONF_MOBILE_NUMBER]
        # Entries created before these were stored fall back to the defaults.
        self._otp_platform = int(
            entry_data.get(CONF_OTP_PLATFORM, DEFAULT_OTP_PLATFORM)
        )
        self._region = entry_data.get(CONF_REGION, region_for_country(DEFAULT_COUNTRY))
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Send a fresh OTP, then swap the new token into the existing entry."""
        errors: dict[str, str] = {}
        if user_input is not None and self._otp_sent:
            token, error = await self._async_validate_otp(user_input["otp"])
            if error:
                errors["base"] = error
            elif self._reauth_entry is not None:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={**self._reauth_entry.data, CONF_TOKEN: token},
                )
                await self.hass.config_entries.async_reload(
                    self._reauth_entry.entry_id
                )
                return self.async_abort(reason="reauth_successful")
        else:
            # First display of the form, or a retry after the PIN could not be
            # sent -- resubmitting asks for a new one rather than dead-ending.
            error = await self._async_send_otp()
            if error:
                errors["base"] = error
            else:
                self._otp_sent = True

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=OTP_SCHEMA,
            errors=errors,
            description_placeholders={"number": self._number or ""},
        )

    # -- reconfigure (change datacentre region) ----------------------------

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the account's datacentre region, then re-verify on it.

        Only the region (and OTP channel) can change here; the number -- and thus
        the entry's identity -- stays the same. A fresh OTP is sent on the chosen
        datacentre so the stored token is valid there.
        """
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry is not None
        self._reconfigure_entry = entry
        self._number = entry.data[CONF_MOBILE_NUMBER]
        self._country = entry.data.get(CONF_COUNTRY, DEFAULT_COUNTRY)

        errors: dict[str, str] = {}
        if user_input is not None:
            self._region = _resolve_region(self._country, user_input.get(CONF_REGION))
            self._otp_platform = int(
                user_input.get(CONF_OTP_PLATFORM, DEFAULT_OTP_PLATFORM)
            )
            error = await self._async_send_otp()
            if error is None:
                return await self.async_step_reconfigure_confirm()
            errors["base"] = error

        current_region = entry.data.get(
            CONF_REGION, region_for_country(self._country)
        )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_REGION, default=current_region
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_REGION_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_OTP_PLATFORM,
                    default=str(entry.data.get(CONF_OTP_PLATFORM, DEFAULT_OTP_PLATFORM)),
                ): vol.In(
                    {
                        str(OTP_PLATFORM_WHATSAPP): "WhatsApp",
                        str(OTP_PLATFORM_SMS): "SMS",
                    }
                ),
            }
        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
            description_placeholders={"number": self._number or ""},
        )

    async def async_step_reconfigure_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate the OTP and update the entry's region + token in place."""
        errors: dict[str, str] = {}
        if user_input is not None:
            token, error = await self._async_validate_otp(user_input["otp"])
            if error:
                errors["base"] = error
            elif self._reconfigure_entry is not None:
                return self.async_update_reload_and_abort(
                    self._reconfigure_entry,
                    data={
                        **self._reconfigure_entry.data,
                        CONF_REGION: self._region,
                        CONF_OTP_PLATFORM: self._otp_platform,
                        CONF_TOKEN: token,
                    },
                )

        return self.async_show_form(
            step_id="reconfigure_confirm",
            data_schema=OTP_SCHEMA,
            errors=errors,
            description_placeholders={"number": self._number or ""},
        )


class CentsysOptionsFlow(OptionsFlow):
    """Options: toggle the opt-in persistent live-status listener.

    Kept minimal -- a single boolean. Changing it reloads the entry (see
    ``__init__.async_setup_entry``), which starts or stops the listener.
    """

    def __init__(self, config_entry: ConfigEntry) -> None:
        # Stored under a private name rather than ``self.config_entry`` to avoid
        # the deprecation warning on HA versions that set it on the base class.
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENABLE_LIVE_LISTENER,
                    default=self._entry.options.get(CONF_ENABLE_LIVE_LISTENER, False),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
