# Examples

Optional, copy‑paste Home Assistant configuration that builds on top of the
HeatCon integration. These files are **not** required for the integration to
work — they are conveniences you can adopt as‑is or adapt.

## `packages/heatcon_schedule.yaml` — dashboard‑friendly schedule helpers

The integration already exposes the weekly switching schedule as native
`time.*` entities (DHW comfort start/end and per‑room day/night start). Those
are the source of truth and snap every value to the grid the controller
supports (DHW = 10 minutes, room = whole hour).

This package adds a thin convenience layer on top:

- **28 `input_datetime` helpers** — one time‑only picker per `time.*` entity.
  They are nicer to drop on a dashboard than the raw `time.*` entities and are
  easy to reference in cards.
- **2 sync automations** — keep the helpers and the `time.*` entities in
  two‑way sync:
  - **push**: you change a helper → it is written to the matching `time.*`
    entity (which snaps it to the controller grid).
  - **pull**: a `time.*` entity changes (poll or external change) → the
    matching helper is updated, so it always reflects the controller value.

The snap‑back is handled automatically: setting a helper to an off‑grid value
writes it, the controller snaps it, and the pull automation settles the helper
on the snapped value (at most two hops, no loop).

### Install

1. Enable packages once in `configuration.yaml`:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

2. Copy `packages/heatcon_schedule.yaml` to `<config>/packages/`.
3. Check the configuration and restart Home Assistant.

### Adjust the entity prefixes to your install

The `time.*` entity ids are derived from your **device** name and **room**
name. On the reference install they are:

```
time.berging_intergas_xceed_domestic_hot_water_<weekday>_comfort_start|end
time.berging_intergas_xceed_room_1_<weekday>_day_start|night_start
```

If your device/room slug differs, find & replace these two prefixes throughout
the package file (they appear in the trigger lists and in each automation's
`target` variable):

```
time.berging_intergas_xceed_domestic_hot_water_
time.berging_intergas_xceed_room_1_
```

Use **Developer Tools → States** and filter on `time.` to find your exact ids.

### Note

The two automations intentionally use templates in their `condition` and
`target` (a chained `replace` that maps a helper id to its paired `time.*` id,
and vice‑versa). This lets a single automation handle all 28 entity pairs per
direction; there is no native Home Assistant equivalent for dynamically
mapping one entity to another.
