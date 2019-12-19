import argparse
import calandigital as cd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

parser = argparse.ArgumentParser(
    description="Plot snapshots from snapshot blocks in ROACH model.")
parser.add_argument("-i", "--ip", dest="ip", required=True,
    help="ROACH IP address.")
parser.add_argument("-b", "--bof", dest="boffile",
    help="boffile to load into the FPGA.")
parser.add_argument("-r", "--rver", dest="roach_version", type=int, default=2,
    choices={1,2}, help="ROACH version to use. 1 and 2 supported.")
parser.add_argument("-sn", "--snapnames", dest="snapnames", nargs="*",
    help="names of snapshot blocks to read.")
parser.add_argument("-dt", "--dtype", dest="dtype", default=">i1",
    help="data type of snapshot data. Must be Numpy compatible.")
parser.add_argument("-ns", "--nsamples", dest="nsamples", type=int, default=256,
    help="number of samples of snapshot to plot.")

def main():
    args = parser.parse_args()
    
    roach = cd.initialize_roach(args.ip, 
        boffile       = args.boffile, 
        roach_version = args.roach_version)

    fig, lines = create_figure(args.snapnames, args.nsamples, args.dtype)

    def animate(_):
        snapdata_list = cd.read_snapshots(roach, args.snapnames, args.dtype)
        for line, snapdata in zip(lines, snapdata_list):
            line.set_data(range(args.nsamples), snapdata[:args.nsamples])
        return lines

    ani = FuncAnimation(fig, animate, blit=True)
    plt.show()

def create_figure(snapnames, nsamples, dtype_string):
    axmap = {1 : (1,1), 2 : (1,2), 4 : (2,2), 16 : (4,4)}
    dtype = np.dtype(dtype_string)
    nsnapshots = len(snapnames)

    fig, axes = plt.subplots(*axmap[nsnapshots])
    if not isinstance(axes, np.ndarray) : axes = np.array(axes)
    fig.set_tight_layout(True)

    lines = []
    for snapname, ax in zip(snapnames, axes.flatten()):
        ax.set_xlim(0, nsamples)
        ax.set_ylim(np.iinfo(dtype).min-10, np.iinfo(dtype).max+10)
        ax.set_xlabel('Samples')
        ax.set_ylabel('Amplitude [a.u.]')
        ax.set_title(snapname)
        ax.grid()

        line, = ax.plot([], [], animated=True)
        lines.append(line)

    return fig, lines

if __name__ == '__main__':
    main()
