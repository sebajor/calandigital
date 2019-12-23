import argparse
import calandigital as cd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

parser = argparse.ArgumentParser(
    description="Plot spectra from an spectrometer model in ROACH.")
parser.add_argument("-i", "--ip", dest="ip", required=True,
    help="ROACH IP address.")
parser.add_argument("-b", "--bof", dest="boffile",
    help="boffile to load into the FPGA.")
parser.add_argument("-r", "--rver", dest="roach_version", type=int, default=2,
    choices={1,2}, help="ROACH version to use. 1 and 2 supported.")
parser.add_argument("-bn", "--bramnames", dest="bramnames", nargs="*",
    help="names of bram blocks to read.")
parser.add_argument("-ns", "--nspecs", dest="nspecs", type=int, default=2,
    choices={1,2,4,16}, help="number of independent spectra to plot.")
parser.add_argument("-dt", "--dtype", dest="dtype", default=">i8",
    help="data type of bram data. Must be Numpy compatible.")
parser.add_argument("-aw", "--addrwidth", dest="awidth", type=int, default=9,
    help="width of bram address in bits.")
parser.add_argument("-dw", "--datawidth", dest="dwidth", type=int, default=64,
    help="width of bram data in bits.")
parser.add_argument("-bw", "--bandwidth", dest="bw", type=float, default=1080,
    help="Bandwidth of the spectra to plot in MHz.")
parser.add_argument("--nbits", dest="nbits", type=int, default=8,
    help="number of bits used to sample the data (ADC bits).")
parser.add_argument("-cr", "--countreg", dest="count_reg", default="cnt_rst",
    help="counter register name. reset at initialization.")
parser.add_argument("-ar", "--accreg", dest="acc_reg", default="acc_len",
    help="accumulation register name. set at initialization.")
parser.add_argument("-al", "--acclen", dest="acclen", type=int, default=2**16,
    help="accumulation length. set at initialization.")

def main():
    args = parser.parse_args()
    
    roach = cd.initialize_roach(args.ip, 
        boffile       = args.boffile, 
        roach_version = args.roach_version)

    nbrams         = len(args.bramnames) / args.nspecs
    specbrams_list = [args.bramnames[i*nbrams:(i+1)*nbrams] for i in range(args.nspecs)]
    nchannels      = 2**args.awidth * nbrams 
    freqs          = np.linspace(0, args.bw, nchannels, endpoint=False)
    dBFS           = 6.02*args.nbits + 1.76 + 10*np.log10(nchannels)

    fig, lines = create_figure(args.nspecs, args.bw, dBFS)

    print("Setting and resetting registers...")
    roach.write_int(args.acc_reg, args.acclen)
    roach.write_int(args.count_reg, 1)
    roach.write_int(args.count_reg, 0)
    print("done")

    def animate(_):
        for line, specbrams in zip(lines, specbrams_list):
            specdata = cd.read_interleave_data(roach, specbrams, 
                args.awidth, args.dwidth, args.dtype)
            specdata = cd.scale_and_dBFS_specdata(specdata, args.acclen, 
                args.nbits, nchannels)
            line.set_data(freqs, specdata)
        return lines

    ani = FuncAnimation(fig, animate, blit=True)
    plt.show()

def create_figure(nspecs, bandwidth, dBFS):
    axmap = {1 : (1,1), 2 : (1,2), 4 : (2,2), 16 : (4,4)}

    fig, axes = plt.subplots(*axmap[nspecs])
    if not isinstance(axes, np.ndarray) : axes = np.array(axes)
    fig.set_tight_layout(True)

    lines = []
    for i, ax in enumerate(axes.flatten()):
        ax.set_xlim(0, bandwidth)
        ax.set_ylim(-dBFS-2, 0)
        ax.set_xlabel('Frequency [MHz]')
        ax.set_ylabel('Power [dBFS]')
        ax.set_title('In ' + str(i))
        ax.grid()

        line, = ax.plot([], [], animated=True)
        lines.append(line)

    return fig, lines

if __name__ == '__main__':
    main()
