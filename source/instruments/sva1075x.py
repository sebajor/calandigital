import visa, time
import numpy as np

class sva1075x():

    def __init__(self, visaname, sleep_time=0.1):
        rm = visa.ResourceManager('@py')
        self.instr = rm.open_resource(visaname)
        self._sleep_time = sleep_time
        time.sleep(self._sleep_time)

    def configure_spectrum(self, freq, pts, res_bw, video_bw, attenuator=0):
        """
            freq:       [initial_freq, end_freq] in Hz
            pts:        number of points    (the system does what it wants :( )
            res_bw:     resolution bw in Hz
            video_bw:   video bw
        """

        self.set_instr_mode('sa')

        span = freq[1]-freq[0]
        central_freq = (freq[1]+freq[0])/2
        
        cmd ="BAND %f HZ" %res_bw
        self.instr.write(cmd)
        time.sleep(self._sleep_time)

        cmd = "FREQ:SPAN %f Hz" % span
        self.instr.write(cmd)
        time.sleep(self._sleep_time)

        cmd = "BAND:VID %f Hz" % video_bw
        self.instr.write(cmd)
        time.sleep(self._sleep_time)

        cmd = 'SWE:POIN %d' % pts
        self.instr.write(cmd)
        time.sleep(self._sleep_time)

        cmd = "FREQ:CENT %f Hz" % central_freq
        self.instr.write(cmd)
        time.sleep(self._sleep_time)

        cmd = ":POW:ATT %f" %attenuator
        self.instr.write(cmd)
        time.sleep(self._sleep_time)


     
    def get_spectra(self, channel=1):
        data = self.instr.query_ascii_values(':TRAC:DATA? '+str(channel), container=np.array)
        return data
    

    def get_parameters(self):
        cmd = "BAND?"
        res_bw = self.instr.query_ascii_values(cmd)[0]
        cmd = "FREQ:SPAN?"
        span = self.instr.query_ascii_values(cmd)[0]
        cmd = 'BAND:VID?'
        video_bw= self.instr.query_ascii_values(cmd)[0]
        cmd = 'FREQ:CENT?'
        center = self.instr.query_ascii_values(cmd)[0]
        return res_bw, span, video_bw, center

    def trace_mode(self, mode='normal', channel=1):
        """
        modes:  -normal
                -max_hold
                -min_hold
                -average
        """
        if(mode=='max_hold'):
            cmd = ':TRAC%i:MODE MAXH' %channel
        elif(mode=='min_hold'):
            cmd = ':TRAC%i:MODE MINH'%channel
        elif(mode=='average'):
            cmd = ':TRAC%i:MODE AVER'%channel
        else:
            cmd = ':TRAC%i:MODE WRIT'%channel
        self.instr.write(cmd)

    def set_instr_mode(self, mode='sa'):
        """
        modes:  
                sa:     spectrum analyzer
                dma:    modulation analysis
                dtf:    distance to fault
                vna:    vector network analyzer
        """
        cmd = ':INST '+str(mode)
        self.instr.write(cmd)

