import visa, time


class rigol_dp832():
    """ class to control Rigol DC generator 
    """
    
    def __init__(self, ip, sleep_time=0.1):
        visa_name = 'TCPIP::'+ip+'::INSTR'
        self.rm = visa.ResourceManager('@py')
        self.instr = self.rm.open_resource(visa_name)
        self._sleep_time = sleep_time
        time.sleep(self._sleep_time)

    def turn_output_on(self, channel):
        """
        """
        cmd = 'outp ch'+str(channel)+',on'
        self.instr.write(cmd)
        time.sleep(self._sleep_time)


    def turn_output_off(self, channel):
        """
        """
        cmd = 'outp ch'+str(channel)+',off'
        self.instr.write(cmd)
        time.sleep(self._sleep_time)


    def get_status(self, channel):
        """
        return True if the channel is on and False if its off
        """
        cmd = 'outp? CH'+str(channel)
        status = self.instr.query(cmd)
        out = (status=='ON\n')
        return out
         
    
    def set_voltage(self, channel, value):
        """ channel: 1,2,3
            value: voltage value to set
        remember that channel 1,2 accepts
        values in the range (0-30) and the 3 accepts values from (0-5)
        """
        cmd = ':INST:NSEL '+str(channel)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        if((channel==3) and (value>5) ):
            raise Exception('Voltage too large')
        elif(value>30):
            raise Exception('Voltage too large')
        cmd = 'volt '+str(value)
        self.instr.write(cmd)

    def get_voltage(self, channel):
        """ get the set value
        """
        cmd = ':INST:NSEL '+str(channel)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        out = self.instr.query('volt?')
        time.sleep(self._sleep_time)
        out = float(out)
        return out

    def set_current(self, channel, value):
        """ 
        """
        cmd = ':INST:NSEL '+str(channel)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        cmd = 'curr '+str(value)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
    
    
    def get_current(self, channel):
        """ get the set value
        """
        cmd = ':INST:NSEL '+str(channel)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        out = self.instr.query('curr?')
        time.sleep(self._sleep_time)
        out = float(out)
        return out


    def set_ovp(self, channel, value):
        """ 
        """
        cmd = ':INST:NSEL '+str(channel)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        cmd = ':VOLT:PROT '+str(value)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        
    
    def set_ocp(self, channel, value):
        """ 
        """
        cmd = ':INST:NSEL '+str(channel)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)
        cmd = ':CURR:PROT '+str(value)
        self.instr.write(cmd)
        time.sleep(self._sleep_time)

    def meas_voltage(self, channel):
        """ get the value that the source is output
        """
        cmd = ':MEAS:VOLT? CH'+str(channel)
        out = self.instr.query(cmd)
        time.sleep(self._sleep_time)
        volt = float(out)
        return volt

    def meas_current(self, channel):
        """ get the value that the source is output
        """
        cmd = ':MEAS:CURR? CH'+str(channel)
        out = self.instr.query(cmd)
        time.sleep(self._sleep_time)
        curr = float(out)
        return curr
    
    def meas_power(self, channel):
        cmd = ':MEAS:POWE? CH'+str(channel)
        out = self.instr.query(cmd)
        time.sleep(self._sleep_time)
        pow_ = float(out)
        return pow_

