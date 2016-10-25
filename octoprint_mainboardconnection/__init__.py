# coding=utf-8
from __future__ import absolute_import

from time import sleep
import octoprint.plugin
from octoprint.util import RepeatedTimer
from octoprint.events import eventManager, Events

__author__ = "Allen McAfee <allen@robo3d.com>"
__license__ = ("GNU Affero General Public License "
               "http://www.gnu.org/licenses/agpl.html")
__copyright__ = ("Copyright (C) 2016 Robo 3D, Inc. - "
                 "Released under terms of the AGPLv3 License")


class MainboardConnectionPlugin(octoprint.plugin.StartupPlugin,
                              octoprint.plugin.SettingsPlugin,
                              octoprint.plugin.SimpleApiPlugin):

    def __init__(self):
        self._timer = None
        self._enabled = None
        self._firmware_plugin = None
        self._automation_plugin = None

    def get_settings_defaults(self):
        return dict(
            enabled=True
        )

    def get_api_commands(self):
        return dict(
            toggle_enabled=[]
        )

    def on_after_startup(self):
        self._firmware_plugin = self._plugin_manager.get_plugin_info(
            "firmwareupdate")

        self._enabled = self._settings.get_boolean(["enabled"])
        self._timer = RepeatedTimer(
            1.0, self._check_connection, run_first=True)
        self._timer.start()

    def on_api_command(self, command, data):
        if command == "toggle_enabled":
            if data['current']:
                self._enabled = False
            else:
                self._enabled = True
            self._settings.set_boolean(["enabled"], self._enabled)
            self._settings.save()
            eventManager().fire(Events.SETTINGS_UPDATED)

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self._enabled = self._settings.get_boolean(["enabled"])

    def _check_connection(self):
        state = self._printer.get_state_string()
        if self._firmware_plugin is None:
            firmware_updating = False
        else:
            firmware_updating = (
                self._firmware_plugin.implementation._is_updating())

        if self._automation_plugin is None:
            automation_running = False
        else:
            automation_running = (
                self._automation_plugin.implementation._is_running())

        if self._enabled and not firmware_updating and not automation_running:
            if state in ["Closed", "Offline"]:
                self._logger.info("Offline or closed; reconnecting")
                self._printer.connect()
            elif "Error" in state or state == "Unknown":
                self._logger.info("Error detected; reopening connection")
                self._printer.disconnect()
                self._printer.connect()
                sleep(15)
                
    def get_update_information(self):
        return dict(
            systemcommandeditor=dict(
                displayName="Octoprint Main Board Connection",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="Robo3D",
                repo="OctoPrint-EEPROM-Marlin",
                current=self._plugin_version,

                # update method: pip
                #update from robo directly
                pip="https://github.com/Robo3D/Octoprint-MainboardConnection/{target_version}.zip"
            )
        )
        

__plugin_name__ = "Mainboard Connection Plugin"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MainboardConnectionPlugin()
