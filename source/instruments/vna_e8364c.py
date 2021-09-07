import visa
import sys
from pyvisa.resources import MessageBasedResource
import time

class vna_E8364C():
    """ python object to control the vna E8364c via lan

    """
    def __init__(self, ip_addr, sleep_time=0.1):
        """
        :parameter ip addr: ip of the vna
        """
        self.sleep_time = sleep_time
        visa_addr = 'TCPIP0::'+ip_addr+'::hpib7,16::INSTR'
        self.rm = visa.ResourceManager('@py')
        self.instr = rm.open_resource(visa_addr)
        self.instr.write('*RST; *CLS;')
        self.instr.write('*IDN?')
        self.instr.write('SYST:FPReset;');
        time.sleep(self.sleep_time)
        self.instr.write('DISPlay:WINDow1:STATE ON;');
        self.instr.write('format:data ascii');
        self.instr.write('initiate:continuous off');
        self.instr.write('output:state off');
 

    def close_connection(self):
        self.instr.close()

    def correlator_setup(self, freq, rbw,avg=1,R='ab'):
        """
            :param freq : frequency to work with
            :param rbw  : Resolution bandwidth
            :param avg  : Average at each point
            :param R    : type of measure
        """
        self.instr.write("calculate1:parameter:define 'ch1_a', "+R);
        self.instr.write("DISP:WIND:TRAC1:FEED 'ch1_a'");
        self.instr.write("sense1:sweep:mode continuous");

        self.instr.write('sense1:sweep:points 1');
        self.instr.write('sense1:frequency:center '+str(freq));
        self.instr.write('sense1:bandwidth:resolution '+str(rbw));

        # average points
        self.instr.write('sense1:average:mode point');
        self.instr.write('sense1:average:count '+str(avg));
        self.instr.write('sense1:average:state on');

        # sweep time
        self.instr.write('sense1:sweep:time:auto on');
    
    def correlator_read(self):
        """ Read the magnitude and the real and imaginary part of the correlation,
            of the two ports. The vna has to be in the correlator setup.
            returns:
                [magnitude, real correlation, imag correlation]
        """
        self.instr.write('initiate1;*wai');
        self.instr.write('*OPC?')
        self.instr.timeout=10000
        state = self.instr.read_ascii_values();
        self.instr.timeout=2000;
        self.instr.write('CALCulate1:DATA? SDATA');
        [re, im] = self.instr.read_ascii_values()
        time.sleep(self.sleep_time)
        self.instr.write('CALCulate1:DATA? FDATA')
        mag = self.instr.read_ascii_values()
        return [mag, re, im]

    


