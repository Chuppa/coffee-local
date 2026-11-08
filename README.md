# Coffee Local

Personal Home Assistant integration for my Coffee Local setup. Requires my custom bridge; not intended for general use.

## Brief connection interruptions

Previously received readings stay visible for up to 90 seconds after the last
ready update during network failures or a machine reconnect. Connected diagnostics
show the current connection immediately. Sustained failures still make entities
unavailable. Authentication, invalid responses and device identity changes fail
immediately. Power commands require a live connection and are never replayed.
