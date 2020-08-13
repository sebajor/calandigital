class DummyRoach():
    """
    Class to simulate a ROACH connection.
    """
    def __init__(self, host, port=7147, tb_limit=20, timeout=10.0, logger=None):
        pass
       
    def is_connected(self):
        return True

    def progdev(self, boffile):
        pass

    def upload_program_bof(self, bof_file, port, timeout = 30):
        pass

    def est_brd_clk(self):
        return 0.0
    
    def snapshot_get(self, dev_name, man_trig=False, man_valid=False, wait_period=1, offset=-1, circular_capture=False, get_extra_val=False, arm=True):
        return {'data': b'\0' * 256}

    def write_int(self, device_name, integer, blindwrite=False, offset=0):
        pass

    def read_int(self, device_name, offset=0):
        return 0

    def write(self, device_name, data, offset=0):
        pass

    def blindwrite(self, device_name, data, offset=0):
        pass

    def read(self, device_name, size, offset=0):
        return b'\0' * size

    def write_dram(self, data, offset=0, verbose=False):
        pass
    
    def read_dram(self, size, offset=0, verbose=False):
        return b'\0' * size
