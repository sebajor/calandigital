import argparse
import calandigital as cd

parser = argparse.ArgumentParser(
    description="Initialize ROACH communication and program boffile.")
parser.add_argument("-i", "--ip", dest="ip", default=None,
    help="ROACH IP address.")
parser.add_argument("-b", "--bof", dest="boffile",
    help="Boffile to load into the FPGA.")
parser.add_argument("-u", "--upload", dest="upload", action="store_true",
    help="If used, upload .bof from PC memory (ROACH2 only).")

def main():
    args = parser.parse_args()

    roach = cd.initialize_roach(args.ip, boffile=args.boffile, upload=args.upload)

if __name__ == '__main__':
    main()
