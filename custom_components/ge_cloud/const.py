import voluptuous as vol
import homeassistant.helpers.config_validation as cv

DOMAIN = "ge_cloud"
INTEGRATION_VERSION = "1.1.10"
CONFIG_VERSION = 1

CONFIG_KIND = "kind"
CONFIG_KIND_ACCOUNT = "account"

DATA_CONFIG = "CONFIG"
DATA_CLIENT = "DATA_CLIENT"
DATA_ACCOUNT = "ACCOUNT"
DATA_SERIALS = "SERIALS"
DATA_ACCOUNT_COORDINATOR = "ACCOUNT_COORDINATOR"
CONFIG_MAIN_API_KEY = "api_key"
CONFIG_ACCOUNT_ID = "account_id"

DATA_SCHEMA_ACCOUNT = {
    vol.Required(CONFIG_ACCOUNT_ID, default="home"): str,
    vol.Required(CONFIG_MAIN_API_KEY, default="api_key"): str,
}

GE_API_URL = "https://api.givenergy.cloud/v1/"
GE_API_INVERTER_STATUS = "inverter/{inverter_serial_number}/system-data/latest"
GE_API_INVERTER_METER = "inverter/{inverter_serial_number}/meter-data/latest"
GE_API_INVERTER_SETTINGS = "inverter/{inverter_serial_number}/settings"
GE_API_INVERTER_READ_SETTING = (
    "inverter/{inverter_serial_number}/settings/{setting_id}/read"
)
GE_API_INVERTER_WRITE_SETTING = (
    "inverter/{inverter_serial_number}/settings/{setting_id}/write"
)
GE_API_DEVICES = "communication-device"
GE_API_DEVICE_INFO = "communication-device"
GE_API_SMART_DEVICES = "smart-device"
GE_API_SMART_DEVICE = "smart-device/{uuid}"
GE_API_SMART_DEVICE_DATA = "smart-device/{uuid}/data"
GE_API_EVC_DEVICES = "ev-charger"
GE_API_EVC_DEVICE = "ev-charger/{uuid}"
GE_API_EVC_DEVICE_DATA = "ev-charger/{uuid}/meter-data?start_time={start_time}&end_time={end_time}&meter_ids[]={meter_ids}"
GE_API_EVC_COMMANDS = "ev-charger/{uuid}/commands"
GE_API_EVC_COMMAND_DATA = "ev-charger/{uuid}/commands/{command}"
GE_API_EVC_SEND_COMMAND = "ev-charger/{uuid}/commands/{command}"
GE_API_EVC_SESSIONS = "ev-charger/{uuid}/charging-sessions?start_time={start_time}&end_time={end_time}&pageSize=32"

GE_REGISTER_BATTERY_CUTOFF_LIMIT = 75

# 0	Current.Export	Instantaneous current flow from EV
# 1	Current.Import	Instantaneous current flow to EV
# 2	Current.Offered	Maximum current offered to EV
# 3	Energy.Active.Export.Register	Energy exported by EV (Wh or kWh)
# 4	Energy.Active.Import.Register	Energy imported by EV (Wh or kWh)
# 5	Energy.Reactive.Export.Register	Reactive energy exported by EV (varh or kvarh)
# 6	Energy.Reactive.Import.Register	Reactive energy imported by EV (varh or kvarh)
# 7	Energy.Active.Export.Interval	Energy exported by EV (Wh or kWh)
# 8	Energy.Active.Import.Interval	Energy imported by EV (Wh or kWh)
# 9	Energy.Reactive.Export.Interval	Reactive energy exported by EV. (varh or kvarh)
# 10 Energy.Reactive.Import.Interval	Reactive energy imported by EV. (varh or kvarh)
# 11 Frequency	Instantaneous reading of powerline frequency
# 12 Power.Active.Export	Instantaneous active power exported by EV. (W or kW)
# 13 Power.Active.Import	Instantaneous active power imported by EV. (W or kW)
# 14 Power.Factor	Instantaneous power factor of total energy flow
# 15 Power.Offered	Maximum power offered to EV
# 16 Power.Reactive.Export	Instantaneous reactive power exported by EV. (var or kvar)
# 17 Power.Reactive.Import	Instantaneous reactive power imported by EV. (var or kvar)
# 19 SoC	State of charge of charging vehicle in percentage
# 18 RPM	Fan speed in RPM
# 20 Temperature	Temperature reading inside Charge Point.
# 21 Voltage	Instantaneous AC RMS supply voltage
EVC_DATA_POINTS = {
    0: "Current.Export",
    1: "Current.Import",
    2: "Current.Offered",
    3: "Energy.Active.Export.Register",
    4: "Energy.Active.Import.Register",
    5: "Energy.Reactive.Export.Register",
    6: "Energy.Reactive.Import.Register",
    7: "Energy.Active.Export.Interval",
    8: "Energy.Active.Import.Interval",
    9: "Energy.Reactive.Export.Interval",
    10: "Energy.Reactive.Import.Interval",
    11: "Frequency",
    12: "Power.Active.Export",
    13: "Power.Active.Import",
    14: "Power.Factor",
    15: "Power.Offered",
    16: "Power.Reactive.Export",
    17: "Power.Reactive.Import",
    18: "RPM",
    19: "SoC",
    20: "Temperature",
    21: "Voltage",
}

# 0	EV Charger	These readings are taken by the EV charger internally
# 1	Grid Meter	These readings are taken by the EM115 meter monitoring the grid, if there is one installed
# 2	PV 1 Meter	These readings are taken by the EM115 meter monitoring PV generation source 1, if there is one installed
# 3	PV 2 Meter	These readings are taken by the EM115 meter monitoring PV generation source 2, if there is one installed
EVC_METER_CHARGER = 0
EVC_METER_GRID = 1
EVC_METER_PV1 = 2
EVC_METER_PV2 = 3

# Commands
# ['start-charge', 'stop-charge', 'adjust-charge-power-limit', 'set-plug-and-go', 'set-session-energy-limit', 'set-schedule', 'unlock-connector', 'delete-charging-profile', 'change-mode', 'restart-charger', 'change-randomised-delay-duration', 'add-id-tags', 'delete-id-tags', 'rename-id-tag', 'installation-mode', 'setup-version', 'set-active-schedule', 'set-max-import-capacity', 'enable-front-panel-led', 'configure-inverter-control', 'perform-factory-reset', 'configuration-mode', 'enable-local-control']
# Command adjust-charge-power-limit  {'min': 6, 'max': 32, 'value': 32, 'unit': 'A'}
# Command set-plug-and-go  {'value': False, 'disabled': False, 'message': None}
# Comamnd  {'min': 0.1, 'max': 250, 'value': None, 'unit': 'kWh'}
# Command set-schedule  {'schedules': []}
# Command unlock-connector  []
# Command delete-charging-profile data None response None
# Command change-mode  [{'active': False, 'available': True, 'image_path': '/images/dashboard/cards/ev/modes/eco-with-sun.png', 'title': 'Solar', 'key': 'SuperEco', 'description': 'Your vehicle will only charge when there is >1.4kW excess solar power available.'}, {'active': False, 'available': True, 'image_path': '/images/dashboard/cards/ev/modes/eco-with-sun-grid.png', 'title': 'Hybrid', 'key': 'Eco', 'description': 'Your vehicle will start charging using grid or solar at >1.4kW. As excess power becomes available, the charge rate will adjust automatically to maximise self consumption.'}, {'active': True, 'available': True, 'image_path': '/images/dashboard/cards/ev/modes/eco-with-grid.png', 'title': 'Grid', 'key': 'Boost', 'description': 'Your vehicle will charge using whichever power source is available up to the current limit you set.'}, {'active': False, 'available': False, 'image_path': '/images/dashboard/cards/ev/modes/eco-with-inverter.png', 'title': 'Inverter Control', 'key': 'ModbusSlave', 'description': 'Your vehicle will charge based upon instructions that it has been given by the GivEnergy Inverter.'}]
# Command restart-charger  []
# Command change-randomised-delay-duration  []
# Command add-id-tags  {'id_tags': [], 'maximum_id_tags': 200}
# Command delete-id-tags  []
# Command rename-id-tag  []
# Command installation-mode ct_meter
# Command setup-version 1
# Command set-active-schedule {'schedule': None}
# Command set-max-import-capacity {'value': '80', 'min': 40, 'max': 100}
# Command enable-front-panel-led {'value': True}
# Command configure-inverter-control {'inverter_battery_export_split': 0, 'max_battery_discharge_power_to_evc': 0, 'mode': 'SuperEco'}
# Command perform-factory-reset []
# Command configuration-mode {'value': 'C'}
# Command enable-local-control {'value': True}
EVC_COMMAND_NAMES = {
    "start-charge": "Start Charge",
    "stop-charge": "Stop Charge",
    "adjust-charge-power-limit": "Adjust Charge Power Limit",
    "set-plug-and-go": "Set Plug and Go",
    "set-session-energy-limit": "Set Session Energy Limit",
    "set-schedule": "Set Schedule",
    "unlock-connector": "Unlock Connector",
    "delete-charging-profile": "Delete Charging Profile",
    "change-mode": "Change Mode",
    "restart-charger": "Restart Charger",
    "change-randomised-delay-duration": "Change Randomised Delay Duration",
    "add-id-tags": "Add ID Tags",
    "delete-id-tags": "Delete ID Tags",
    "rename-id-tag": "Rename ID Tag",
    "installation-mode": "Installation Mode",
    "setup-version": "Setup Version",
    "set-active-schedule": "Set Active Schedule",
    "set-max-import-capacity": "Set Max Import Capacity",
    "enable-front-panel-led": "Enable Front Panel LED",
    "configure-inverter-control": "Configure Inverter Control",
    "perform-factory-reset": "Perform Factory Reset",
    "configuration-mode": "Configuration Mode",
    "enable-local-control": "Enable Local Control"
}
EVC_SELECT_VALUE_KEY = {
    "change-mode" : "mode",
    "adjust-charge-power-limit" : "limit",
    "set-session-energy-limit" : "limit",
    "change-randomised-delay-duration" : "delay",
    "set-plug-and-go" : "enabled",
}

# Unsupported commands
EVC_BLACKLIST_COMMANDS = ["installation-mode", "perform-factory-reset", "rename-id-tag", "delete-id-tags", "change-randomised-delay-duration"]