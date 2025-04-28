import requests
import logging
import random

ElectronicFilterMaintenance = {
    "code": "electronic_filter_maintenance",
    "interval": 600,
    "name": "Electronics filter",
    "guide_url": "prusa.io/ht90-electronic-filter-cleaning",
    "label1": "Electronics Filter Maintenance Recommended",
    "label2": "Scan QR code for guide"
}

ChamberFilterMaintenance = {
    "code": "chamber_filter_maintenance",
    "interval": 600,
    "name": "Chamber filter",
    "guide_url": "prusa.io/ht90-hepa-filter-replacement",
    "label1": "Chamber Filter Maintenance Recommended",
    "label2": "Scan QR code for guide"
}

MagBallsMaintenance = {
    "code": "mag_ball_maintenance",
    "interval": 300,
    "name": "Magballs Lubrication",
    "guide_url": "prusa.io/ht90-magballs-lubrication",
    "label1": "Magballs Lubrication Recommended",
    "label2": "Scan QR code for guide"
}

LinearRailsMaintenance = {
    "code": "linear_rails_maintenance",
    "interval": 1000,
    "name": "Linear Rails Lubrication",
    "guide_url": "prusa.io/ht90-linear-rails-lubrication",
    "label1": "Linear Rails Lubrication Recommended",
    "label2": "Scan QR code for guide"
}

MaintenanceIntervals = [
    ElectronicFilterMaintenance,
    ChamberFilterMaintenance,
    MagBallsMaintenance,
    #LinearRailsMaintenance
]

VAR_PREFIX = "maintenance_interval_"

class Maintenance:
    def __init__(self, screen):
        self._screen = screen
        self.printer_config = self._screen.printers[0][list(self._screen.printers[0])[0]]

    def _fetch_current_hours(self):
        r = requests.get(
            f"http://{self.printer_config['moonraker_host']}:{self.printer_config['moonraker_port']}/server/history/totals").json()
        return r["result"]["job_totals"]["total_print_time"] / (60 * 60)

    def check_maintenance(self):
        required_maintenance = []
        current_printed_hours = self._fetch_current_hours()
        persistent = self._screen._config.get_config()["persistent_data"]

        for mi in MaintenanceIntervals:
            last_maintenance = float(persistent.get(VAR_PREFIX + mi["code"], 0))
            if last_maintenance == 0:
                last_maintenance = self._randomize_first_maintenance(mi)
            if current_printed_hours > last_maintenance + mi["interval"]:
                required_maintenance.append(mi)

        return required_maintenance

    def show_maintenance(self):
        show_maintenance = []

        current_printed_hours = self._fetch_current_hours()
        persistent = self._screen._config.get_config()["persistent_data"]

        for mi_o in MaintenanceIntervals:
            mi = mi_o.copy()
            last_maintenance = float(persistent.get(VAR_PREFIX + mi["code"], 0))
            if last_maintenance == 0:
                last_maintenance = self._randomize_first_maintenance(mi)
            mi["since_last_maintenance"] = current_printed_hours - last_maintenance
            mi["to_next_maintenance"] = mi["interval"] - mi["since_last_maintenance"]
            show_maintenance.append(mi)

        return show_maintenance

    def _randomize_first_maintenance(self, mi):
        current_printed_hours = self._fetch_current_hours()
        config = self._screen._config.get_config()
        virt_last_maintenance = current_printed_hours - mi["interval"]
        if virt_last_maintenance < 0:
            return 0
        else:
            virt_last_maintenance += random.randrange(1, 30)
        config.set("persistent_data", VAR_PREFIX + mi["code"], str(virt_last_maintenance))
        self._screen._config.save_user_config_options()
        return virt_last_maintenance

    def reset_maintenance(self, maintenance_interval):
        current_printed_hours = self._fetch_current_hours()
        config = self._screen._config.get_config()
        config.set("persistent_data", VAR_PREFIX + maintenance_interval["code"], str(current_printed_hours))
        self._screen._config.save_user_config_options()
