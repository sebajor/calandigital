"""
Main calandigital script with helper functions.
"""
import sys, time, imp
import corr
import numpy as np

def parse_arguments():
    """
    Parse arguments from command line when running a calandigital script. 
    First argument can be a python file with configuration parameters. 
    Following arguments are additional parameters, in the format 
    "--param_name param_value".
    :return: module with the script parameters.
    """
    print("Parsing command line arguments...")
    # check if argument exists
    if len(sys.argv) <= 1:
        print("No command line arguments to read") 
        return imp.new_module("config params")

    # check for config file
    if not sys.argv[1].startswith("--"):
        print("\tReading parameters from " + sys.argv[1] + " config file.")
        config_file = sys.argv[1]
        commandline_args = sys.argv[1:]

        # create parameter module from config file
        try:
            fp, pathname, description = imp.find_module(config_file)
        except ImportError:
            print("Unable to load config file " + config_file)
            print("If you are trying to input command line parameters," + 
                " make sure their name starts with double dash (--)")
            exit()
        params = imp.load_module("config params", fp, pathname, description)
        print("\tdone.")

    else:
        params = imp.new_module("config params")
        commandline_args = sys.argv[1:]

    # add commandline arguments into the parameters
    attrnames = commandline_args[0::2]
    attrvals  = commandline_args[1::2]
    if len(attrnames) >= 1:
        print("\tReading command line arguments...")
        for attrname, attrval in zip(attrnames, attrvals):
            if not attrname.startswith("--"):
                print("Error in command line " + attrname)
                print("Use double dash (--) at the begining of parameter" +
                    "names in command line")
                exit()
                
            # try to evaluate attribute value, 
            # if fails keep the value as a string.
            try:
                attrval = eval(attrval)
            except (NameError, SyntaxError):
                pass

            setattr(params, attrname[2:], attrval)

        print("\tdone.")
    
    print("done.")

    return params

def initialize_roach(ip, port=7147, boffile=None, roach_version=2):
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
        print("\t1. ROACH wasn't ready to connect yet")
        print("\t2. Incorrect IP")
        print("\t3. ROACH not connected to the network")
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
        print("\t1. no .bof file programmed in FPGA")
        print("\t2. .bof not found in ROACH internal memory (ROACH1)")
        print("\t3. .bof not in not in the same directory as the script (ROACH2)")
        exit()
    print("done. Estimated clock: " + str(fpga_clock))
