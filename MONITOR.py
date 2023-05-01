# riaps:keep_import:begin
import capnp
from riaps.run.comp import Component

import riaps_capnp
# riaps:keep_import:end


class MONITOR(Component):
    # riaps:keep_constr:begin
    def __init__(self):
        super().__init__()
        self.logger.info("MONITOR - starting")
        self.averages = {"VA_RMS": None,
                         "Freq": None}
    # riaps:keep_constr:end

    # riaps:keep_gen_sub:begin
    def on_gen_sub(self):
        msg = self.gen_sub.recv_pyobj()
        self.logger.info(f"MONITOR - on_gen_sub: {msg}")
        # get index of voltage and frequency from the message
        voltage_index = msg["params"].index("VA_RMS")
        freq_index = msg["params"].index("FREQ")
        # get the values from the message
        voltage = msg["values"][voltage_index][0]
        freq = msg["values"][freq_index][0]
        # update the averages
        self.update_averages(voltage, "VA_RMS")
        self.update_averages(freq, "Freq")
    # riaps:keep_gen_sub:end

    # riaps:keep_relay_sub:begin
    def on_relay_sub(self):
        msg_bytes = self.relay_sub.recv()
        capnp_msg = riaps_capnp.RelayMsg.from_bytes(msg_bytes)
        msg = capnp_msg.to_dict()
        self.logger.info(f"MONITOR - on_relay_sub: {msg}")
        # get the values from the message
        voltage = msg["varms"]
        freq = msg["frequency"]
        # update the averages
        self.update_averages(voltage, "VA_RMS")
        self.update_averages(freq, "Freq")
    # riaps:keep_relay_sub:end

    # riaps:keep_poller:begin
    def on_poller(self):
        now = self.poller.recv_pyobj()
        self.logger.info(f"MONITOR - on_poller: {str(now)} | "
                         f"averages: {self.averages}")
    # riaps:keep_poller:end

    # riaps:keep_impl:begin
    # Function to update the averages
    def update_averages(self, value, key):
        if self.averages[key] is None:
            self.averages[key] = value
        else:
            self.averages[key] = (self.averages[key] + value) / 2
    # riaps:keep_impl:end
