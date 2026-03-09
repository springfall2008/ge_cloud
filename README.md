# GivEnergy Cloud service

This integration connects the GivEnergy cloud service to Home Assistant

Enter the name of your account e.g. home (useful only if you have more than one) and the API key from the GE Cloud Accounts area.

If all is working then the integration will create some sensors and update them once every minute (with register updates every 5 minutes)

Supports:
- Inverters including Gen1/Gen2/EMS/AIO
- Smart Plugs (but not very good, you can't actually toggle the switch via cloud as they don't support it). Will give you the local API key to use with the Tuya Local integration.
- Home Charger (EVC) - Basic support with monitoring and some controls (e.g. modes, charge power, stop/start etc).

For support please raise a Github ticket.

If you want to buy me a beer then please use Paypal - [tdlj@tdlj.net](mailto:tdlj@tdlj.net)
![image](https://github.com/springfall2008/batpred/assets/48591903/b3a533ef-0862-4e0b-b272-30e254f58467)

## Example dashboard

<img width="1528" alt="image" src="https://github.com/springfall2008/ge_cloud/assets/48591903/25e91b51-c325-4fe9-97e1-3dab6d1b1061">

## Install through HACS

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

- In HACS, click on Integration
- Click on the three dots in the top right corner, choose *Custom Repositories*
- Add <https://github.com/springfall2008/ge_cloud> as a custom repository of Category 'Integration' and click 'Add'
- Click *Explore and download repositories* (bottom right), type 'Ge Cloud' in the search box, select the Predbat Repository, then click 'Download' to install the app.
- Restart Home Assistant
- Go to Integrations, click add and select 'GE Cloud'.
- Enter a name for your Setup (e.g. Home) and your API key (create an API key inside Security settings on the GE Cloud web site)
- If you only want to see one of the device types uncheck the others, otherwise leave them all enabled (if you don't have a device type that's okay)
- Uncheck polling if you have an EMS, otherwise leave it set.
