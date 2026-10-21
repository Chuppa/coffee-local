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

## Behaviour

Fresh validated status controls availability. Bridge outages recover through HA’s
coordinator polling. Commands wait for delivery and fail if delivery cannot be
confirmed. Delivery means handed to the machine, not confirmation of physical
execution. Check the machine before retrying an ambiguous drink command.

This initial release needs attended testing on the actual machine/firmware.
Do not run the old Cremalink bridge and the new bridge against the same machine
at the same time. New entities have different IDs; update automations deliberately.

Licensed under AGPL-3.0-or-later; see LICENSE.
