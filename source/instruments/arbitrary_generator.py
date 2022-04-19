import visa, time
import numpy as np

###
### Author: Sebastian Jorquera
###

class arbitrary_generator():
    
    def __init__(self, instr_name, sleep_time):
        """
        Class to handle an arbitrary wave generator
        instr_name  : Visa name of the generator
        sleep_time  : sleep time after send an instruction
        """
        rm = visa.ResourceManager('@py')
        self.instr = rm.open_resource(instr_name)
        self.sleep_time = sleep_time
    
    def turn_output_on(self):
        """
        Turn on the output of the generator.
        """
        self.instr.write('outp on')
        time.sleep(self.sleep_time)

    def turn_output_off(self):
        """
        Turn off the output of the generator.
        """
        self.instr.write('outp off')
        time.sleep(self.sleep_time)
    
    def set_freq_hz(self, freq):
        self.instr.write('freq '+str(freq))
        time.sleep(self.sleep_time)

    def set_amplitude_vpp(self, volt):
        self.instr.write('volt '+str(volt))
        time.sleep(self.sleep_time)

    def set_offset_volt(self, volt):
        self.instr.write('volt:offs '+str(volt))
        time.sleep(self.sleep_time)

    def select_waveform(self, option='sine', user_name='VOLATILE'):
        """
        select the waveform type
        option      : sine, square, ramp, pulse, noise, dc, user
        user_name   : when selecting the user wave you have to give the name of
                      signal.
        """
        waves = {'sine':'sin', 'square':'squ', 'ramp':'ramp', 'pulse':'puls',
                'noise':'nois', 'dc':'dc', 'user':'user'}
        if(option is not 'user'):
            self.instr.write('func: '+waves[option])
            time.sleep(self.sleep_time)
        else:
            self.instr.write('func: user '+user_name)
            time.sleep(self.sleep_time)

    
    def sweep_config(self, sweep_time, start, stop, sweep_type='linear'):
        """
            sweep time  :   time for the sweeping in seconds
            start       :   start frequency
            stop        :   stop frequency
            sweep_type  :   linear or log
        """
        sweep = {'linear':'lin', 'log':'log'}   
        self.instr.write('swe:spa '+sweep[sweep_type])
        time.sleep(self.sleep_time)
        self.instr.write('swe:time '+str(sweep_time))
        time.sleep(self.sleep_time)
        self.instr.write('swe:star '+str(start))
        time.sleep(self.sleep_time)
        self.instr.write('swe:stop '+str(stop))
        time.sleep(self.sleep_time)

    def turn_sweep_on(self):
        self.instr.write('swe:state on')
        time.sleep(self.sleep_time)

    def turn_sweep_off(self):
        self.instr.write('swe:state off')
        time.sleep(self.sleep_time)

    
    def set_arbitrary_waveform(self, data, name=None):
        """
        Upload a waveform to the arbitrary generator volatile memory
        data    :   numpy array with the values in (-1,1) range
        name    :   if the name is not None it saves in the non-volatile memory
                    names should be shorter than 12 characters
        """
        if((np.abs(data)>1).any()):
            raise Exception("The data values should be normalized to (-1,1) range")
        str_data = np.array2string(data)
        str_data = str_data[1:-1]           #no consider the [ ] 
        str_data = str_data.replace(' ',',')#put commas between values    
        self.instr.write("DATA VOLATILE,"+str_data)
        time.sleep(self.sleep_time)
        if(name is not None):
            self.instr.write('DATA:COPY '+str(name)+', VOLATILE')
            time.sleep(self.sleep_time)

     
    def erase_waveform(self, user_name):
        """
        Erase a stored waveform
        """
        self.instr.write('DATA:DEL '+user_name)
        time.sleep(self.sleep_time)
        
    
    def burst_config(self, cycles, trigger_type='immediate'):
        """
        cycles          :   number of cycles to output per burst
        trigger_type    :   'inmediate','external','bus'

        """
        trigg = {'immediate':'IMM', 'external':'EXT','bus':'BUS'}
        self.instr.write('BURST:NCYC '+str(cycles))
        time.sleep(self.sleep_time)
        self.instr.write('TRIG:SOUR '+trigg[trigger_type])
        time.sleep(self.sleep_time)

    def turn_burst_on(self):
        """ 
        just turn on the burst mode, but you still would need the trigger to
        send a burst.
        To use this mode you have to disable the other modes if they are on.
        """
        self.instr.write('burst:state on')
        time.sleep(self.sleep_time)

    def turn_burst_off(self):
        """ 
        just turn on the burst mode, but you still would need the trigger to
        send a burst
        """
        self.instr.write('burst:state off')
        time.sleep(self.sleep_time)

    def send_sw_trigger(self):
        self.instr.write('*trg')
        time.sleep(self.sleep_time)
         


