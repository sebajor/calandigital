"""
Main calandigital script with helper functions.
"""
import corr, time, imp

def parse_arguments(arg_list):
    """
    Parse arguments when running a calandigital script. first argument
    can be a python file with configuration parametes. Following arguments
    are additional parameters, in the format "--param_name param_value".
    :param arg_list: list of arguments as strings.
    :return: parsed arguments as a dictionary.
    """
    args_dict = {}

    # check for config file
    if not arg_list[0].startswith("--"):
        config_file = arg_list[0]
        commandline_arg_list = arg_list[1:]

        # create parameter module from config file
        fp, pathname, description = imp.find_module(config_file)
        params = imp.load_module("config params", fp, pathname, description)

    else:
        params = imp.new_module("config params")
        commandline_arg_list = arg_list

    # add commandline arguments into the parameters
    attrnames = commandline_arg_list[0::2]
    attrvals  = commandline_arg_list[1::2]
    for attrname, attrval in zip(attrnames, attrvals):
        if not attrname.startswith("--"):
            print("Error in command line " + attrname)
            print("Use double dash (--) at the begining of attributes \
                names in command line")
            exit()
                
        # try to evaluate attribute value, 
        #if fails keep the value as a string.
        try:
            attrval = eval(attrval)
        except (NameError, SyntaxError):
            pass
            
        setattr(params, attrname[2:], attrval)

    return params

def initialize_roach(ip, port=1747, boffile=None, roach_version=2):
    """
    Initialize ROACH, that is, start ROACH communication, program boffile
    into the FPGA, and creates the FpgaClient object to communicate with.
    :param ip: ROACH IP address.
    :param port: ROCH TCP/IP port for communication.
    :param boffile: .bof file to program the FPGA. If None porgramming 
        is skipped.
    :param roach_version: version of the ROACH, 1 and 2 supported.
    :return: FpgaClient object to communicate with ROACH's FPGA.
    """
    print("Initializing ROACH communication...")
    roach = corr.katcp_wrapper.FpgaClient(ip, port)
    time.sleep(0.1)
    if not roach.is_connected():
        print("Unable to connect to ROACH :/")
        print("Possible causes:")
        print("\t1. Incorrect IP")
        print("\t2. ROACH not connected to the nwtwork")
        exit()
    print("done")

    if boffile is not None:
        print("Programming boffile into ROACH...")
        if roach_version is 1:
            print("\tUsing ROACH1, programming from ROACH internal memory...")
            roach.progrdev(boffile)
        elif roach_version is 2:
            print("\tUsing ROACH2, programming from PC memory...")
            roach.upload_program_bof(boffile, 60000)
        else:
            print("ROACH version not supported.")
            exit()
        print("done")
    else:
        print("Skipping programming boffile.")

    print("Estimating FPGA clock frequency...")
    try:
        fpga_clock = roach.est_brd_clk()
    except RuntimeError:
        print("Unable to estimate frequency :/")
        print("Possible causes:")
        print("\t1. .bof file not programmed in FPGA")
        print("\t2. .bof not found in ROACH internal memory (ROACH1)")
        print("\t3. .bof not in not in the same directory as the script (ROACH2)")
        exit()
    print("done. Estimated clock: " + str(fpga_clock))
