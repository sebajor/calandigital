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
    help="ROACH version to use. 1 and 2 supported.")
parser.add_argument("-sn", "--snapname", dest="snapname", default="adcsnap",
    help="snapshot naming suffix used to deduce the name of the snapshot blocks.")
parser.add_argument("-ns", "--nsnapshots", dest="nsnapshots", type=int, default=2,
    help="number of snapshots. Used to deduce the name of the snapshot blocks.")
parser.add_argument("-dt", "--dtype", dest="dtype", default=">i1",
    help="data type of snapshot data. Must be Numpy compatible.")
parser.add_argument("-sa", "--samples", dest="nsamples", type=int, default=256,
    help="samples of snapshot to plot. By default plot all samples.")

def main():
    args = parser.parse_args()
    
    roach = cd.initialize_roach(args.ip, 
        boffile       = args.boffile, 
        roach_version = args.roach_version)

    # get snapshot names
    snapshots = [args.snapname + str(i) for i in range(args.nsnapshots)]

    fig, lines = create_figure(args.nsnapshots, args.nsamples, args.dtype)

    def animate(_):
        snapdata_list = cd.read_snapshots(roach, snapshots, args.dtype)
        for line, snapdata in zip(lines, snapdata_list):
            line.set_data(range(args.nsamples), snapdata[:args.nsamples])
        return lines

    ani = FuncAnimation(fig, animate, blit=True)
    plt.show()

def create_figure(nsnapshots, nsamples, dtype_string):
    axmap = {1 : (1,1), 2 : (1,2), 4 : (2,2), 16 : (4,4)}
    dtype = np.dtype(dtype_string)

    fig, axes = plt.subplots(*axmap[nsnapshots])
    fig.set_tight_layout(True)

    lines = []
    for i, ax in enumerate(axes.flatten()):
        ax.set_xlim(0, nsamples)
        ax.set_ylim(np.iinfo(dtype).min-10, np.iinfo(dtype).max+10)
        ax.set_xlabel('Samples')
        ax.set_ylabel('Amplitude [a.u.]')
        ax.set_title('In ' + str(i))
        ax.grid()

        line, = ax.plot([], [], animated=True)
        lines.append(line)

    return fig, lines

if __name__ == '__main__':
    main()
