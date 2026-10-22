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

## Controls and status

One Power switch, plus Status, Attachment, Progress, Busy, connection status,
and water tank / grounds container / milk refrigeration warnings. Status values
use readable names such as Ready, Standby, Heating up and Milk jug (hot).
Unmapped protocol values appear as Unknown rather than exposing numeric codes.
Drink and Stop buttons, the unmapped Action sensor, and the duplicate Idle
sensor are removed automatically when upgrading from 0.1.0. Existing power and
status entity IDs and user customisations are retained; the former Accessory
sensor is now named Attachment (its existing entity ID is retained).

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
