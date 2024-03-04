# Givenergy Cloud service

This integration connects the GivEnergy cloud service to Home Assistant

* This alpha version only supports Inverter gen 1 registers and smart switches (just power data & local key)

Enter the name of your account e.g. home (useful only if you have more than one) and the API key from the GE Cloud Accounts area.

If all is working then the integration will create some sensors and update them once a minute

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
