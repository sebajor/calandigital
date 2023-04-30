import pyvisa
import time

class visa_generator():
    """
    """
    def __init__(self, visa_connection, sim=False, _sleep=0.1):
        if(sim):
            rm = pyvisa.ResourceManager('@sim')
        else:
            rm = pyvisa.ResourceManager('@py')
        self.instr = rm.open_resource(visa_connection)
        self._sleep = _sleep
        
    def turn_output_on(self):
        """
        Turn on the output of the generator.
        """
        self.instr.write('outp on')
        time.sleep(self._sleep)

    def turn_output_off(self):
        """
        Turn off the output of the generator.
        """
        self.instr.write('outp off')
        time.sleep(self._sleep)

    def get_output_status(self):
        ans = self.instr.query_ascii_values('outp?')
        return ans

    def get_freq(self):
        ans = self.instr.query_ascii_values('freq?')
        return ans

    def set_freq_hz(self, freq):
        self.instr.write(('freq ' + str(freq)))
        time.sleep(self._sleep)


    def set_freq_mhz(self, freq):
        """
        Set the generator output frequency. 
        :param freq: frequency to set in MHz.
        """
        self.set_freq_hz(10**6 * freq)

    def set_freq_ghz(self, freq):
        """
        Set the generator output frequency. 
        :param freq: frequency to set in MHz.
        """
        self.set_freq_hz(10**9 * freq)

    def get_power_dbm(self):
        ans = self.instr.query_ascii_values('power?')
        return ans
    
    def set_power_dbm(self, power):
        """
        Set the generator output power. 
        :param power: power level to set in dBm.
        """
        self.instr.write(('power ' + str(power)))
        time.sleep(self._sleep)

    
    def set_phase_deg(self, phase):
        """
        Set generator phase (if the instrument supports it)
        :param phase: phase in degrees
        """
        self.instr.write(('phase '+str(phase)+' deg'))
        time.sleep(self._sleep)

