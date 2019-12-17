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
    help="ROACH verstion to use. 1 and 2 supported.")
parser.add_argument("-bn", "--bramname", dest="bramname", default="dout",
    help="bram naming suffix used to deduce the name of the bram blocks.")
parser.add_argument("-nb", "--nbrams", dest="nbrams", type=int, default=8,
    help="number of bram per spectrum. Used to deduce the name of the bram blocks.")
parser.add_argument("-ns", "--nspecs", dest="nspecs", type=int, default=2,
    help="number of spectra. Used to deduce the name of the bram blocks.")
parser.add_argument("-dt", "--dtype", dest="dtype", default=">i4",
    help="data type of bram data. Must be Numpy compatible.")
parser.add_argument("-aw", "--addrwidth", dest="awidth", type=int, default=9,
    help="width of bram address in bits.")
parser.add_argument("-dw", "--datawidth", dest="dwidth", type=int, default=64,
    help="width of bram data in bits.")
parser.add_argument("-bw", "--bandwidth", dest="bw", type=float, default=1080,
    help="Bandwidth of the spectra to plot in MHz.")
parser.add_argument("-nb", "--nbits", dest="nbits", type=int, default=8,
    help="number of bits used to sample the data (ADC bits).")
parser.add_argument("-cr", "--countreg", dest="count_reg", default="cnt_rst",
    help="counter register name. reset at initialization.")
parser.add_argument("-ar", "--accreg", dest="acc_reg", default="acc_len",
    help="accumulation register name. set at initialization.")
parser.add_argument("-al", "--acclen", dest="acc_len", type=int, default=2**16,
    help="accumulation length. set at initialization.")

def main():
    args = parser.parse_args()
    
    roach = cd.initialize_roach(args.ip, 
        boffile       = args.boffile, 
        roach_version = args.roach_version)

    specbrams = get_specbram_names(args.bramname, args.nbrams, args.nspecs)
    nchannels = 2**args.awidth * args.nbrams 
    freqs     = np.linspace(0, args.bw, nchannels, endpoint=False)

    fig, lines = create_figure(args.bw, args.nspecs, args.dtype)

    def animate(_):
        specdata_list = cd.read_interleave_data(roach, specbrams, 
            args.awidth, args.dwidth, args.dtype)
        for line, specdata in zip(lines, specdata_list):
            specdata = cd.scale_and_dBFS_specdata(specdata)
            line.set_data(freqs, specdata)
        return lines

    ani = FuncAnimation(fig, animate, blit=True)
    plt.show()

def get_specbram_names(bramname, nbrams, nspecs):
    specbrams_list = []
    for ispec in range(nspecs):
        specbrams = []
        for ibram in range(nbrams):
            specbrams.append(bramname + "_" + str(ispec) + "_" + str(ibram))
        specbrams_list.append(specbrams)

    return specbrams_list

def create_figure(bandwidth, nsamples, dtype_string):
    axmap = {1 : (1,1), 2 : (1,2), 4 : (2,2), 16 : (4,4)}
    dBFS = 6.02*nbits + 1.76 + 10*np.log10(nchannels)

    fig, axes = plt.subplots(*axmap[nsnapshots])
    fig.set_tight_layout(True)

    lines = []
    for ax in axes.flatten():
        ax.set_xlim(0, bandwidth)
        ax.set_ylim(-dBFS, 0)
        ax.set_xlabel('Frequency [MHz]')
        ax.set_ylabel('Power [dBFS]')
        ax.grid()

        line, = ax.plot([], [], animated=True)
        lines.append(line)

    return fig, lines

if __name__ == '__main__':
    main()
