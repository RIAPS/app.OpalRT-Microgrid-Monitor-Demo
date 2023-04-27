# riaps:keep_import:begin
import capnp
import os
import time

from riaps.run.comp import Component
import riaps.interfaces.modbus.device_capnp as msg_struct
from riaps.interfaces.modbus.config import load_config_file

import riaps_capnp
import applibs.helper as helper

debugMode = helper.debugMode
# riaps:keep_import:end


def compute_relay_status(relay_parameters, relay_status_thresholds):

    connected = relay_parameters["IS_GRID_CONNECTED_BIT"] == relay_status_thresholds["GRID_CONNECTED"]

    sync_thresholds = relay_status_thresholds["SYNCHRONIZED"]
    if abs(relay_parameters['SYNCHK_FREQ_SLIP']) < sync_thresholds["FREQ_SLIP_THRESHOLD"] \
            and abs(relay_parameters['SYNCHK_VOLT_DIFF']) < sync_thresholds["VOLT_DIFF_THRESHOLD"] \
            and abs(relay_parameters['SYNCHK_ANG_DIFF']) < sync_thresholds["ANGLE_DIFF_THRESHOLD"]:
        sync = True
    else:
        sync = False

    zero_power_thresholds = relay_status_thresholds["ZERO_POWER_FLOW"]
    if abs(relay_parameters['P']) < zero_power_thresholds["ACTIVE_POWER_THRESHOLD"] \
            and abs(relay_parameters['Q']) < zero_power_thresholds["REACTIVE_POWER_THRESHOLD"]:
        zero_power_flow = True
    else:
        zero_power_flow = False
    return {'connected': connected, 'synchronized': sync, 'zero_power_flow': zero_power_flow}


# riaps:keep_constr:begin
class RELAY_MANAGER(Component):
    def __init__(self, config):
        super().__init__()

        self.pid = os.getpid()
        self.counter = 0

        self.relayMessages = {}
        self.relayStatus = {}

        modbus_device_config = load_config_file(config)
        self.device_name = modbus_device_config["Name"]
        self.relay_status_thresholds = modbus_device_config["RELAY_STATUS_THRESHOLDS"]
    # riaps:keep_constr:end

    def handleActivate(self):
        self.logger.info(f"RELAYF1_MANAGER | handleActivate | Wait for operator message before polling relay")
        period = self.poller.getPeriod()
        # self.poller.halt()

    # riaps:keep_poller:begin
    def on_poller(self):
        # send commands to quary
        now = self.poller.recv_pyobj()
        if debugMode:
            self.logger.info(f"on_poller()[{str(self.pid)}]: {str(now)}")

        self.query_relay(self.device_name)

    def query_relay(self, dvc):
        modbus_msg = msg_struct.DeviceQry.new_message()
        modbus_msg.device = dvc
        modbus_msg.operation = "READ"
        modbus_msg.params = ["IS_GRID_CONNECTED_BIT",
                             "VA_RMS",
                             "FREQ",
                             "SYNCHK_FREQ_SLIP",
                             "SYNCHK_VOLT_DIFF",
                             "SYNCHK_ANG_DIFF",
                             "P",
                             "Q"]
        modbus_msg.values = [[-1]] * len(modbus_msg.params)
        modbus_msg.msgcounter = self.counter
        modbus_msg_bytes = modbus_msg.to_bytes()
        self.device_port.send(modbus_msg_bytes)
        self.counter += 1
    # riaps:keep_poller:end

    # riaps:keep_device_port:begin
    def on_device_port(self):
        # Response from device component
        msg_bytes = self.device_port.recv()
        msg = msg_struct.DeviceAns.from_bytes(msg_bytes)

        if msg.operation == "WRITE":
            return

        relay_parameters = {}
        for parameter, value in zip(msg.params, msg.values):
            relay_parameters[parameter] = value[0]
            # values is a list of lists. For the relay they are single values
            # status, varms, frequency, frequencyDiff, voltageDiff, angleDiff, activePower, reactivePower

        if debugMode:
            self.logger.info(f"{helper.Yellow}\n"
                             f"RELAY1_PWR_MANAGER.py "
                             f"on_device_port \n"
                             f"msg: {msg}"
                             f"{helper.RESET}")

        relay_id = msg.device

        relay_status = compute_relay_status(relay_parameters, self.relay_status_thresholds)
        self.relayStatus[relay_id] = relay_status

        relay_msg = riaps_capnp.RelayMsg.new_message()
        relay_msg.sender = relay_id
        relay_msg.timestamp = time.time()
        relay_msg.connected = relay_status["connected"]
        relay_msg.synchronized = relay_status["synchronized"]
        relay_msg.zeroPowerFlow = relay_status["zero_power_flow"]
        relay_msg.activePower = relay_parameters["P"]  # keep
        relay_msg.reactivePower = relay_parameters["Q"]  # keep
        relay_msg.freqSlip = relay_parameters["SYNCHK_FREQ_SLIP"]  # keep
        relay_msg.voltDiff = relay_parameters["SYNCHK_VOLT_DIFF"]  # keep
        relay_msg.angDiff = relay_parameters["SYNCHK_ANG_DIFF"]  # keep
        relay_msg.varms = relay_parameters["VA_RMS"]  # remove?
        relay_msg.frequency = relay_parameters["FREQ"]  # remove?
        relay_msg.msgcounter = msg.msgcounter
        relay_msg_bytes = relay_msg.to_bytes()

        self.relayMessages[relay_id] = relay_msg.to_dict()
        self.logger.info(f"{helper.BrightYellow}\n"
                         f"relayMessage: {relay_msg}\n"
                         f"relayStatus: {self.relayStatus[relay_id]}\n"
                         f"{helper.RESET}")

        self.relay_pub.send(relay_msg_bytes)
    # riaps:keep_device_port:end




