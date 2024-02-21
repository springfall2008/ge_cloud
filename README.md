# Givenergy Cloud service

This integration connects the GivEnergy cloud service to Home Assistant

* This alpha version only supports inverters and a few basic sensors

Enter the name of your account e.g. home (useful only if you have more than one) and the API key from the GE Cloud Accounts area.

If all is working then the integration will create some sensors and update them once a minute

For support please raise a Github ticket.

## Install through HACS

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

- In HACS, click on Integration
- Click on the three dots in the top right corner, choose *Custom Repositories*
- Add <https://github.com/springfall2008/ge_cloud> as a custom repository of Category 'Integration' and click 'Add'
- Click *Explore and download repositories* (bottom right), type 'Ge Cloud' in the search box, select the Predbat Repository, then click 'Download' to install the app.
- Restart Home Assistant
- Go to Integrations, click add and select 'GE Cloud'.
