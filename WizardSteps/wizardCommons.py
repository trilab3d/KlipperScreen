import logging
import contextlib

class TemperatureSetter:
    def set_temperature(self, setting, heaters):
        if not hasattr(self, "preheat_options"):
            self.preheat_options = self._screen._config.get_preheat_options()
        self._screen._ws.klippy.gcode_script("_SAVE_TEMPERATURE")
        if len(heaters) == 0:
            self._screen.show_popup_message(_("Nothing selected"))
        else:
            for heater in heaters:
                logging.info(f"Looking for settings for heater {heater}")
                target = None
                max_temp = float(self._screen.printer.get_config_section(heater)['max_temp'])
                name = heater.split()[1] if len(heater.split()) > 1 else heater
                with contextlib.suppress(KeyError):
                    for i in self.preheat_options[setting]:
                        if i == name:
                            # Assign the specific target if available
                            target = self.preheat_options[setting][name]
                            logging.info(f"name match {name}")
                        elif i == heater:
                            target = self.preheat_options[setting][heater]
                            logging.info(f"heater match {heater}")
                if target is None and setting == "cooldown" and not heater.startswith('temperature_fan '):
                    target = 0
                if heater.startswith('extruder'):
                    if setting == 'cooldown' or self.validate(heater, target, max_temp):
                        self._screen._ws.klippy.set_tool_temp(self._screen.printer.get_tool_number(heater), target)
                elif heater.startswith('heater_bed'):
                    if target is None:
                        with contextlib.suppress(KeyError):
                            target = self.preheat_options[setting]["bed"]
                    if setting == 'cooldown' or self.validate(heater, target, max_temp):
                        self._screen._ws.klippy.set_bed_temp(target)
                elif heater.startswith('heater_chamber'):
                    if target is None:
                        with contextlib.suppress(KeyError):
                            target = self.preheat_options[setting]["chamber"]
                    if setting == 'cooldown' or self.validate(heater, target, max_temp):
                        self._screen._ws.klippy.set_chamber_temp(target)
                elif heater.startswith('heater_generic '):
                    if target is None:
                        with contextlib.suppress(KeyError):
                            target = self.preheat_options[setting]["heater_generic"]
                    if setting == 'cooldown' or self.validate(heater, target, max_temp):
                        self._screen._ws.klippy.set_heater_temp(name, target)
                elif heater.startswith('temperature_fan '):
                    if target is None:
                        with contextlib.suppress(KeyError):
                            target = self.preheat_options[setting]["temperature_fan"]
                    if setting == 'cooldown' or self.validate(heater, target, max_temp):
                        self._screen._ws.klippy.set_temp_fan_temp(name, target)

            if setting == 'cooldown':
                self._screen._ws.klippy.gcode_script(f"SET_FAN_SPEED FAN=intake_flap SPEED=1")
            elif "flap" in self.preheat_options[setting]:
                self._screen._ws.klippy.gcode_script(f"SET_FAN_SPEED FAN=intake_flap SPEED={self.preheat_options[setting]['flap']}")
            # This is probably dead stump
            # global speed_request
            # if setting in self.preheat_options and "speed" in self.preheat_options[setting]:
            #     speed_request = float(self.preheat_options[setting]["speed"])
            # else:
            #     speed_request = 1

    def validate(self, heater, target=None, max_temp=None):
        if target is not None and max_temp is not None:
            if 0 <= target <= max_temp:
                self._screen.printer.set_dev_stat(heater, "target", target)
                return True
            elif target > max_temp:
                self._screen.show_popup_message(_("Cannot set above the maximum:") + f' {max_temp}')
                return False
        logging.debug(f"Invalid {heater} Target:{target}/{max_temp}")
        return False