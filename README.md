# Coffee Local

Personal Home Assistant integration for my Coffee Local setup. Requires my custom bridge; not intended for general use.

## Brief connection interruptions

Previously received readings stay visible for up to 90 seconds after the last
ready update during network failures or a machine reconnect. Connected diagnostics
show the current connection immediately. Sustained failures still make status entities
unavailable. Authentication, invalid responses and device identity changes fail
immediately. When the bridge is reachable, Power remains available during machine reconnects.

## Power control

Requires Coffee Local Bridge 2026.11.10 or later. Update the bridge first, then
this integration through Marketplace and restart Home Assistant.

Power requests retry until a fresh machine report confirms the target. An
opposite request cancels the pending target; confirmed targets stop retrying.
Only power is retried. Pending requests are cleared by bridge restart.
