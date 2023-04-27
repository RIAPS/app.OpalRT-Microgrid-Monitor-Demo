# riaps:keep_import:begin
import capnp
import time
import zmq

from riaps.run.comp import Component
import riaps.interfaces.modbus.device_capnp as msg_struct
from riaps.interfaces.modbus.config import load_config_file

import applibs.helper as helper

import riaps_capnp

# riaps:keep_import:end

debugMode = helper.debugMode


# riaps:keep_constr:begin
class GEN_PWR_MANAGER(Component):
    def __init__(self, config, Ts):
        super().__init__()
        self.msgcounter = 0
        modbus_device_config = load_config_file(config)
        self.device_name = modbus_device_config["Name"]
    # riaps:keep_constr:end

    # riaps:keep_device_qry_port:begin
    def on_device_qry_port(self):
        msg_bytes = self.device_qry_port.recv()
        msg = msg_struct.DeviceAns.from_bytes(msg_bytes)

        self.logger.info(f"{helper.ansBlack}\n"
                         f"GEN_PWR_MANAGER | on_device_qry_port \n"
                         f"recv ans from modbus device: {msg}"
                         f"{helper.RESET}")
    # riaps:keep_device_qry_port:end

    # riaps:keep_poller:begin
    def on_poller(self):
        now = self.poller.recv_pyobj()
        if debugMode:
            self.logger.info(f"{helper.White}\n"
                             f"GEN_PWR_MANAGER | on_poller: {str(now)} \n "
                             f"{helper.RESET}")

        msg = msg_struct.DeviceQry.new_message()
        msg.device = self.device_name
        msg.operation = "READ"
        msg.params = ["FREQ", "VA_RMS", "P", "Q"]  # frequency, voltageMag, activePower, reactivePower
        msg.values = [[-1]] * len(msg.params)
        msg.timestamp = time.time()
        self.msgcounter += 1
        msg.msgcounter = self.msgcounter
        msg_bytes = msg.to_bytes()

        if debugMode:
            self.logger.info(f"{helper.qryBlack}\n"
                             f"GEN_PWR_MANAGER - on_poller \n"
                             f"send qry msgcounter {self.msgcounter} to {self.device_name}\n"
                             f"msg.operation: {msg.operation} \n"
                             f"msg.commands:{msg.params}"
                             f"{helper.RESET}")

        try:
            self.device_qry_port.send(msg_bytes)
        except zmq.ZMQError as e:
            self.logger.info(f"{helper.White}"
                             f"on_device_port queue full: {e}"
                             f"{helper.RESET}")
    # riaps:keep_poller:end



# riaps:keep_impl:begin

# riaps:keep_impl:end
