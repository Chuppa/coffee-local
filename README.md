# Coffee Local

![Coffee Local](custom_components/coffee_local/brand/logo.png)

Home Assistant integration for a Coffee Local Bridge controlling a De’Longhi
PrimaDonna Soul with the ECAM612 protocol profile. No additional pip dependencies
are installed in Home Assistant. Machine protocol/encryption run in a separate bridge.

## Install with HACS

Add `https://github.com/Chuppa/coffee-local` as a custom repository with category **Integration**, install
**Coffee Local**, restart HA, then add Coffee Local in Devices & services. Enter the
bridge’s LAN URL and API token configured in the bridge. Credentials remain on HA.

The bridge is installed separately through its Home Assistant app repository.
The managed bridge lives in the private Home Assistant app collection. This
repository contains only the generic HA integration and its tests, with no
credentials or installation-specific device data.

## Versions

Releases use `year.month.release`, such as `2026.10.0`, `2026.10.1`,
and `2026.11.0`. The last number starts at zero each month. The integration
and bridge have independent release counters.

## Controls and status

Power switch, main machine Status, and water/grounds alerts:

- Water tank empty
- Water tank missing
- Grounds container full
- Grounds container missing

Connection status stays in the diagnostics section. Drink/Stop buttons,
Attachment, Action, Busy, Progress, Idle, and the unsupported milk refrigeration
warning are removed automatically during upgrade. Existing power, status and
water/grounds entity IDs and custom names are preserved.

On the PrimaDonna Soul, alarm/accessory values observed in standby contradict
physical conditions. Water/grounds alerts retain their last reported awake readings in standby,
including across Home Assistant restarts. Fresh awake reports replace the cached
readings. A sensor with no previous reading stays unavailable until its first
awake report; no OK/Problem value is invented. The alarm
mappings still require validation on the actual machine. Downloadable diagnostics
include whitelisted decoded fields and monitor bytes for this verification,
without credentials or device identifiers.

Fresh validated status controls availability. Bridge outages recover through
Home Assistant polling. Power commands wait for delivery and fail if delivery
cannot be confirmed. Delivery means handed to the machine, rather than
confirmation of physical execution. Expired commands are discarded.

Update Coffee Local through HACS and restart Home Assistant. Bridge 0.1.4 is
recommended for reliable command notifications; this update requires no bridge
configuration changes.

Do not run the old Cremalink bridge and the new bridge against the same machine
at the same time.

Licensed under AGPL-3.0-or-later; see LICENSE.
