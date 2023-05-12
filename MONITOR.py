# riaps:keep_import:begin
import capnp
from riaps.run.comp import Component

import riaps_capnp
# riaps:keep_import:end


class MONITOR(Component):
    # riaps:keep_constr:begin
    def __init__(self,name,Ts):
        super().__init__()
        self.logger.info("MONITOR - starting")
        self.averages = {"VA_RMS": None,
                         "Freq": None}
        self.name = name
        self.Ts = Ts
        self.sensorUpdate = False
        self.dataValues = {}
        self.ownValue = 0.0

    # riaps:keep_constr:end

    # riaps:keep_gen_sub:begin
    def on_gen_sub(self):
        msg = self.gen_sub.recv_pyobj()
        self.logger.info(f"MONITOR - on_gen_sub: {msg}")
        # get index of voltage and frequency from the message
        power_index = msg["params"].index("VA_RMS")
        freq_index = msg["params"].index("FREQ")
        # get the values from the message
        power = msg["values"][power_index][0]
        freq = msg["values"][freq_index][0]
        # update the averages
        # self.update_averages(voltage, "VA_RMS")
        # self.update_averages(freq, "Freq")
        self.sensorValue = power
        self.sensorUpdate = True
    # riaps:keep_gen_sub:end

    def on_update(self):
        msg = self.update.recv_pyobj()
        if self.sensorUpdate:
            self.ownValue = self.sensorValue
            self.dataValues = {}
            self.sensorUpdate = False
        if len(self.dataValues) != 0:
            sum = 0.0
            for value in self.dataValues.values():
                sum += (self.ownValue - value)
            der = sum * self.Ts
            self.ownValue -= der
        msg = (self.name,self.ownValue)
        self.nodeDataPub.send_pyobj(msg)

    def on_nodeDataSub(self):
        msg = self.nodeDataSub.recv_pyobj()
        name,value = msg
        if name != self.name:
            self.dataValues[name] = value

    def on_display(self):
        msg = self.display.recv_pyobj()
        self.logger.info(f'Local Estimate: {self.ownValue}')


    # riaps:keep_poller:begin
    # def on_poller(self):
    #     now = self.poller.recv_pyobj()
    #     self.logger.info(f"MONITOR - on_poller: {str(now)} | "
    #                      f"averages: {self.averages}")
    # riaps:keep_poller:end

    # riaps:keep_impl:begin
    # Function to update the averages
    # def update_averages(self, value, key):
    #     if self.averages[key] is None:
    #         self.averages[key] = value
    #     else:
    #         self.averages[key] = (self.averages[key] + value) / 2
    # riaps:keep_impl:end
