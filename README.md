### Meeting

Schedule meetings, track agendas, minutes and action items

### Installation

You need a Frappe bench (version 16 or later). Install the app with the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/akhtarmohsin/meeting --branch develop
bench --site $YOUR_SITE install-app meeting
```

Then open `/meeting` on your site.

To use Frappe Meet video links and Frappe Calendar, install [Frappe Suite](https://github.com/frappe/suite) on the same site. Meeting works without it.

To try the app with sample data, run:

```bash
bench --site $YOUR_SITE meeting-demo
```

System Managers can also load it from **Settings → Demo data**.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/meeting
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

MIT. See [license.txt](license.txt).
