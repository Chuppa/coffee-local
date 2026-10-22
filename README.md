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

## Automatic updates and maintenance

Use the latest stable Coffee Local Bridge from your existing app repository.
Compatibility follows Bridge API v1; bridge and integration release numbers do
not need to match. No fixed bridge release needs to be maintained in this guide.

Your existing Home Assistant update automation can install Coffee Local through
its HACS update entity. A Home Assistant restart loads the newly installed
integration code. Restart timing stays under your control; this integration
does not restart Home Assistant or install software by itself.

One GitHub workflow runs every six hours to test the current integration against
the latest official stable Home Assistant image and run CodeQL source-security
analysis. The test resolves an immutable image digest for each run and retains
the image record and security reports for seven days. HIGH/CRITICAL findings,
failed scans or failed lifecycle tests block publication and open a maintenance
issue. A successful later cycle closes that issue.

Changed integration or release documentation gets an automatic
`year.month.release` number and a tested stable GitHub release for HACS. An
unchanged check does not create another version. Interrupted publication retries
without replacing existing tags. Dependabot checks GitHub Action pins daily;
only pin changes that pass the checks on current main can merge automatically.

The integration has no extra pip dependencies or its own runtime container.
Its Python and OS security updates come from Home Assistant; it does not need
the bridge app's daily precautionary container rebuild. Machine protocol code is
maintained in the separate bridge. Existing HA update automation and valid HACS
access are needed for automatic installation; repository checks cannot enable
device-side update settings or control your chosen restart time.

[HACS update entities](https://www.hacs.dev/docs/use/entities/update/)
support the standard Home Assistant `update.install` action.

Do not run the old Cremalink bridge and the new bridge against the same machine
at the same time.

Licensed under AGPL-3.0-or-later; see LICENSE.
