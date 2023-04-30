import pyvisa, time


class rs_hmp4040():
    """Class to control rohde schwarz power supply.
    Dont know why, but the querys dont work (eg when you ask for the id 
    to the machine you dont get a response). So be carefull and first 
    check that the instrument is indeed connected
    """
    def __init__(self, visa_name, sleep_time=0.1):
        """
        The visaname in ethernet shoudl be something like
        visa_name = 'TCPIP::'+ip+'::'+str(port)+'::SOCKET'
        """
        self.rm = pyvisa.ResourceManager('@py')
        self.instr = self.rm.open_resource(visa_name)
        self._sleep_time = sleep_time
        time.sleep(self._sleep_time)

    def turn_output_on(self, channel):
        cmd = ':INST:NSEL '+str(channel)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        cmd = 'outp 1'
        self.instr.write(cmd)
        time.sleep(self._sleep_time)

    def turn_output_off(self, channel):
        cmd = ':INST:NSEL '+str(channel)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        cmd = 'outp 0'
        self.instr.write(cmd)
        time.sleep(self._sleep_time)

    def set_voltage(self, channel, value):
        cmd = ':INST:NSEL '+str(channel)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        cmd = 'volt '+str(value)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)

    def set_current(self, channel, value):
        """ 
        """
        cmd = ':INST:NSEL '+str(channel)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        cmd = 'curr '+str(value)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
