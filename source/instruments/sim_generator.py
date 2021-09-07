import time
from generator import Generator

class SimGenerator(Generator):
    """
    Dummy simulation class for testing purposes.
    """
    def __init__(self, instr, instr_info):
        Generator.__init__(self, instr, instr_info)
        
    def turn_output_on(self):
        """
        Turn on the output of the generator.
        """
        time.sleep(self.sleep_time)

    def turn_output_off(self):
        """
        Turn off the output of the generator.
        """
        time.sleep(self.sleep_time)

    def set_freq_hz(self, freq=None):
        """
        Set the generator output frequency. 
        :param freq: frequency to set in Hz.
        """
        time.sleep(self.sleep_time)

    def set_freq_mhz(self, freq=None):
        """
        Set the generator output frequency. 
        :param freq: frequency to set in MHz.
        """
        time.sleep(self.sleep_time)

    def set_power_dbm(self, power=None):
        """
        Set the generator output power. 
        :param power: power level to set in dBm.
        """
        time.sleep(self.sleep_time)

    def set_freq_mult(self, freq_mult): 
        """
        Set frequency multiplier.
        """
        time.sleep(self.sleep_time)
