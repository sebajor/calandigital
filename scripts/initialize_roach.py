import argparse
import calandigital as cd

parser = argparse.ArgumentParser(
    description="Initialize ROACH communication and program boffile.")
parser.add_argument("-i", "--ip", dest="ip", required=True,
    help="ROACH IP address.")
parser.add_argument("-b", "--bof", dest="boffile",
    help="boffile to load into the FPGA.")
parser.add_argument("-r", "--rver", dest="roach_version", type=int, default=2,
    choices={1,2}, help="ROACH version to use. 1 and 2 supported.")

def main():
    args = parser.parse_args()

    roach = cd.initialize_roach(
        args.ip, 
        boffile       = args.boffile, 
        roach_version = args.roach_version)

if __name__ == '__main__':
    main()
