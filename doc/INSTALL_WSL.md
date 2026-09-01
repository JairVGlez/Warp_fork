# Windows Subsystem Linux `Warp` Install and Run Instructions
Author(s):

- Ruoyu Fang - fryfang@outlook.com *main contact for this doc*

- Steven Lund - lund@frib.msu.edu

- Daniel Winklehner - Winklehn@mit.edu


## Table of contents
[1. Install WSL on Windows machine](#1-install-wsl-on-windows-machine)

[2. Prepare WSL for `Warp` installation](#2-prepare-wsl-for-warp-installation)

[3. Install `pygist`](#3-install-pygist-optional)

[4. Install `Warp`](#4-install-warp)

[5. Test and clean up after installation](#5-test-and-clean-up-after-installation)

[6. Frequently asked questions](#6-frequently-asked-questions)

[7. Running `Warp` under WSL](#7-running-warp-under-wsl)

[8. Convert frames in cgm file to jpg](#8-convert-frames-in-cgm-file-to-jpg)

[9. Convert jpg into mp4 file](#9-converting-jpg-into-mp4-files)

## 1. Install WSL on Windows machine
1. In Windows menu, search and open "Turn Windows features on or off"
2. Scroll down the menu and check the following two features are turned on:
    - Virtual Machine Platform
    - Windows Subsystem for Linux
3. Click "OK". Wait for the system to prompt a restart. Restart the system.
4. Open Windows menu, search "Powershell", then right click to open Powershell as adminstrator. Type

    ```bash
    wsl --install
    # This will install the latest Ubuntu Long Term Support by default. Ubuntu 26.04 LTS at time of this writing 2026-08-12.
    ```

5. Follow the prompts until finish setting up the WSL username and password, then restart the PC. The WSL is now installed.
6. **CAUTION:** If the system has more than one WSL distribution installed, follow the appropriate command to start the Ubuntu LTS Linux installed or make it default.

## 2. Prepare WSL for `Warp` installation
1. In Windows menu, search and open "wsl" to open the wsl terminal. This will automatically log you into your WSL Ubuntu Linux as a regular user.
2. Type the following commands to update and install the necessary packages with the password created just above.
	```bash
    sudo apt update
    sudo apt upgrade
    sudo apt install build-essential
    ```
3. Highly recommend to use `miniconda3` to create a virtual environment with environments needed for `Warp`.
    1. Download `miniconda3`
    ```bash
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    ```
    2. Install `miniconda3` (recommend defaults)

	```bash
    bash Miniconda3-latest-Linux-x86_64.sh
    ```
	
    3. After `miniconda3` is installed, restart the WSL terminal. You will notice that the terminal now has an prefix like

    ```bash
    (base) username@examplePC:
    ```

    4. This means conda loaded a base virtual environment. It is recommended that we should prevent conda from autoloading a base virtual environment. To do so, type

    ```bash
    conda config --set auto_activate_base false
    ```

    5. Create a virtual environment that will be used for `Warp` (or for more). You can specify which version of python to use, and a custom environment name by replacing `warp_env` with other aliases. At the time of this writing 2026-08-12, it is recommended to use `Python=3.14`.

    ```bash
    conda create -n warp_env -c conda-forge python=3.14
    ```

    6. Activate the `warp_env` virtual environment with

    ```bash
    conda activate warp_env
    ```

    7. Install the necessary packages such as compilers (required), numpy (required), X11(recommended) etc. 
    
    ```bash
    conda install -c conda-forge compilers setuptools numpy xorg-libx11 xorg-xorgproto scipy
    ```
    
    **Note 1:** In my case, I need to install the xorg-xorgproto because the xorg-libx11 was missing "X.h" header file.

    **Note 2:** If the parallel `Warp` is needed, add one more package to install:

    ```bash
    conda install -c conda-forge mpi4py
    ```

    8. Install the Forthon package. **Note:** *I think `conda install -c conda-forge Forthon` will work just fine.*
    
    ```bash
    pip install Forthon
    ```
    
    9. At this point, the seriel `Warp` is ready to be installed. It is also recommended to install `pygist` for `Warp`.

## 3. Install `pygist` (optional)
Although `Warp` is a `Python` interface code, `Warp` makes use of the `pygist` graphics package. To enale use of gist graphics, follow the procedure below.

1. Move to or create a directory to install `pygist` such as "~/src/". In "~/src/", clone `pygist` with
    
    ```bash
    # if ~/src/ directory is not created before, do
    mkdir ~/src/
    # then
    cd ~/src/
    git clone https://bitbucket.org/dpgrote/pygist.git
    ```

2. Move into pygist directory with `cd pygist` and type
    
    ```bash
    python setup.py config
    ```

3. Inspect the terminal output, especially with the X11 returns. If all looks good. Install `pygist` with
    
    ```bash
    python setup.py install
    ```

    **Note:** In some cases, the X11 libraries installed under the `warp_env` cannot be detected by the `pygist` setup.py, which will cause include wrong header files issues in the next step. To fix this, check the [Frequently asked question](#6-frequently-asked-questions).

4. Inspect the terminal output. Verify `pygist` is installed properly with

    ```bash
    gist
    ```

    This will open a blank gist window if it is installed properly.

5. Now `pygist` is installed.

## 4. Install `Warp`
1. Move to "~/src/" with `cd ~/src/`, clone `Warp` with

    ```bash
    git clone https://bitbucket.org/berkeleylab/warp.git
    ```

2. Move into "warp/pywarp90" directory with

    ```bash
    cd ~/src/warp/pywarp90
    ```

3. If you are under a virtual environment like conda, create a "Makefile.local3" in this directory. Add the following two lines to this file and save it. 

    ```bash
    FCOMP = -F gfortran

    FCOMPEXEC = --fcompexec x86_64-apple-darwin13.4.0-gfortran
    ```

    **Note:** Modify `x86_64-apple-darwin13.4.0-gfortran` to whichever gfortran compiler your virtual environment is using. If you are using `miniconda3`, you can find it under "~/miniconda3/envs/warp_env/bin". In my case, I am using `x86_64-conda-linux-gnu-gfortran`, so the above line for me is `FCOMPEXEC = --fcompexec x86_64-conda-linux-gnu-gfortran`

4. Under "~/src/warp/pywarp90" directory, try

    ```bash
    make -j install3
    ```

    **Note:** The above line failed for me but it should point the compiler to look at the Makefile.local3 we just created above to use the gfortran I installed. If this also fails for you, try the next step below.

5. Compile serial `Warp` with
    
    ```bash
    make install
    ```

    **Note:** This will be a long execution. Check output for errors and failures. There should be none.

6. If parallel `Warp` is needed, modify the `Makefile.Forthon3.pympi` file under `~/src/warp/pywarp90/ line 3 and 4 to be:
    
    ```bash
    FCOMP = -F gfortran
    FCOMPEXEC = --fcompexec mpifort
    ```
    
    **Note:** I suspect line 2 also needs to be updated to point to the mpi libraries under the `warp_env` we are using, but the parallel `Warp` compiled fine for me without modifying line 2.

    Then compile the parallel `Warp` with

    ```bash
    make pinstall
    ```

    **Note:** This will be a long execution. Check output for errors and failures. There should be none.

## 5. Test and clean up after installation
1. After `Warp` is built, move to "~/src/warp/warp_test" with `cd ~/src/warp/warp_test/` and run
    
    ```bash
    python runalltests.py
    ```

    **Note:** Most likely you will see errors. Check the [Frequently asked question](#6-frequently-asked-questions) section below.

## 6. Frequently Asked Questions
1. **numpy.typing has no arrtibute: TYPE_CHECKING**
    After compilation of `Warp`, if you run `python runalltests.py` under `~/src/warp/warp_test/`, you may see the error below:

    ```py
    AttributeError: module 'numpy.typing' has no attribute 'TYPE_CHECKING'
    ```
    
    The cause of this lies inside the "~/miniconda3/envs/warp_env/lib/python3.14/site-packages/warp/warp.py" file, package `Numpy` was imported as a wildcard as 
    
    ```py
    from numpy import *
    ```

    This implicitly overrides Python's built-in `typing` module with Numpy's `numpy.typing`. The solution to this is to re-import Python's built-in `typing` module just before the TYPE_CHECKING at around line 120 by changing the following code in `warp.py`

    from
        
    ```py
    if typing.TYPE_CHECKING: 
        from ._fortran_imports import *
    ```
    
    to
    
    ```py
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from ._fortran_imports import *
    ```
    
    Then verify the steps above fix the error by returning to `~/src/warp/warp_test/` and executing the tests with
    
    ```py
    python runalltests.py
    ```

2. **X11 under virtual environment**
    
    If you installed the X11 libraries using `conda install -c conda-forge xorg-libx11 xorg-xorgproto`, chances are that when you install `pygist` with `python setup.py config`, the scirpt can find the X11 libraries, but under the Linux system base library directory `/usr/include`. 
    
    This sometimes may trigger a few errors when compiling the `pygist` with `python setup.py install` as the compiler mistakenly searches header files under your Linux system base environment at `/usr/include`, while it should be searching under the virtual environment `warp_env`.

    To fix this, one should modify the `~/src/pygist/src/play/x11/xconfig.sh` file line 15-16 
    
    from

    ```bash
    if test -z "$X11BASE"; then
        X11BASE=/no/suggested/x11dir
    ```
    
    to

    ```bash
    if test -z "$X11BASE"; then
        if test -n "$CONDA_PREFIX"; then
            X11BASE="$CONDA_PREFIX"
        else
            X11BASE=/no/suggested/x11dir
        fi
    ```

    This ensures the setup.py sets the X11 library path correctly to `warp_env`, so when it installs `pygist`, it will be installed under the `miniconda3/envs/warp_env`.

## 7. Running `Warp` under WSL
In this section, we will show a sketch to run `Warp` under WSL we just set up above.

1. Open WSL via Windows Powershell or WSL Terminal.
2. Activate `warp_env` environment with

    ```bash
    conda activate warp_env
    ```

3. It's a good practice to create another directory for `Warp` simulation scripts outside of the `~/src/` directory. For example, one can create a dedicated `warp_examples` with

    ```bash
    mkdir ~/warp_examples
    ```

    Then move into the `warp_examples` directory with

    ```bash
    cd ~/warp_examples
    ```

4. Let's run our first example from the `Pierce_diode.py` example that comes with `Warp`. To do so, copy the file from `~/src/warp/examples` to `~/warp_examples` with

    ```bash
    cp ~/src/warp/examples/Pierce_diode.py ~/warp_examples
    ```

5. First let's run the example without the interactive gist window with

    ```bash
    python Pierce_diode.py
    ```
    
    You will notice two windows show up and the terminal outputs lots of information. Then the two windows disappear. This is expected. You will also notice the `~/warp_examples` directory now has two more cgm files generated from the simulation named as `Pierce_diode.000.cgm` and `Pierce_diode_current.000.cgm`.

6. Open the `Pierce_diode.000.cgm` with

    ```bash
    gist Pierce_diode.000.cgm
    ```

    A CGM Viewer window displays the simulation results on the screen. You can use your cursor to select the window, and use `f` and `b` to forward and backward the frame, respectively.

    Once you are done with viewing all the frames, you can close the window and type `exit` in the terminal to quit `gist`.

7. Open the `Pierce_diode_current.cgm` with

    ```bash
    gist Pierce_diode_current.cgm
    ```

    This is the second window that show up during the simulation, which plots the current data only from the simulation. You can forward and backward the frame as usual.

8. Alternatively, you can run `Warp` interactively with

    ```bash
    python -i Pierce_diode.py
    ```

    This will run the simulation, two plotting windows show up, but they stay opened once the simulation is done instead of closing the windows automatically.

    **Note:** I found the interactive mode can only do zoom in and out of the X and Y axis with left and right click on the axis. Not sure why the `f` and `b` keys are not working in this mode.

8. Running **Parallel** `Warp` requires the installation in [4. Install `Warp`](#4-install-warp) to be carried all the way through `make pinstall`. Once the parallel `Warp` is installed, using the parallel processing is easy with

    ```bash
    mpiexec -n 4 python Pierce_diode.py
    ```

    The above code will use 4 threads to run the simulation. 
    
    **Note:** You should check the maximum number of threads available in your WSL by typing `nproc` in the terminal. The number it returns should be the most efficient multithread settings to use parallel `Warp`. You can prescribe more threads, for example, if `nproc` returns 4 and you use `mpiexec -n 32 python Pierce_diode.py`, the simulation will run, but probably at a slower speed than `mpiexec -n 4 python Pierce_diode.py`.

## 8. Convert frames in cgm file to jpg
The warp simulation output files are in ".cgm" format. The file can be opened with
```
gist filename
```
You can place your cursor in the window and use `f` key to forward one frame, and `b` key to backward one frame.

**Note:** in the warp simulation `Python` script, usually there are plotting functions called so that useful data are plotted inside the cgm file that an user can view and inspect the simulation visually.

If exporting frames from the cgm file to jpg format is needed, the following code updated to `Python=3.14` from David P. Grote's 2005/06/07 convertcgmtojpg.py can be saved as a convertcgmtojpg.py in the working directory of the simulation script.

To use the code below, it is recommended to install the `ghostscript` and `ImageMagick` packages under `warp_env` with

```bash
conda install -c conda-forge ghostscript imagemagick
```

convertcgmtojpg.py below:

 ```py
#!/usr/bin/env python
##########################################################################
# Author: David P. Grote
# Date: 6/7/2005
# Adapted to make jpeg files and crop them by Alex Friedman, 10/17/2007
# Modified by Ruoyu(Fry) Fang on 2026/08/01 to fix issues with specifying
# start frame, end frame, and framestep, and compatibility with Python 3.14
##########################################################################
# This script converts sequential frames from a cgm file into jpeg files.
# They are all put into a new directory that has the same name as the
# cgm file prefix.
# Note that it relies on gist and gs. All input files are first converted
# into a series of ps files, one per frame. Then ps is converted to jpeg.
# Then the jpeg files are cropped.
#
# The resulting files can be converted to a .mov file using QuickTime Pro
# on a Mac, or by other means
#
##########################################################################

import sys
import os
import string
import re

# --- Print out usage line if needed.
if len(sys.argv) < 3 or len(sys.argv) > 5:
    print('Error: command line had the wrong format, must be one of')
    print('convertcgmtojpg.py filename numframes')
    print('convertcgmtojpg.py filename framestart frameend framestep')

# --- Get the filename
if len(sys.argv) == 3:
    file = sys.argv[2]
    m = re.search(r'(.+)[.](\w+)',file)
    prefix = m.group(1)
    suffix = m.group(2)
elif len(sys.argv) in [4,5]:
    file = sys.argv[1]
    m = re.search(r'(.+)[.](\w+)',file)
    prefix = m.group(1)
    suffix = m.group(2)

# --- Get the frames to be processed.
if len(sys.argv) == 3:
    numframes = int(sys.argv[1])
    framestart = 1
    frameend = numframes
    framestep = 1
elif len(sys.argv) in [4,5]:
    framestart = int(sys.argv[2])
    frameend = int(sys.argv[3])
if len(sys.argv) == 5:
    framestep = int(sys.argv[4])
else:
    framestep = 1
numframes = frameend - framestart + 1

##########################################################################
# --- CGM
# --- Use gist to extract frames into ps files and then use gs to convert
# --- to ppm.
##########################################################################
# --- Convert each frame to a ps file using gist
os.system('mkdir %s'%prefix)
if suffix=='cgm':
    print('extracting frames to ps file')
    gist = os.popen('gist -nd -in '+file,'w')
    gist.write('ps %s/temp.ps\n'%prefix)
    gist.write('send %d-%d-%d\n'%(framestart,frameend,framestep))
    gist.write('quit\n')
    gist.close()


##########################################################################
# --- Convert ps to jpeg.
##########################################################################
# --- NOPAUSE disables the prompt after each frame is processed
# --- < /dev/null gets gs to exit without requiring a ctrl-d by the user
# --- The - gets gs to not print the GS> prompt.
# --- The -r100 arranges for 100 DPI
print('converting ps to ppm')
os.chdir(prefix)
res=150
res=200
os.system('gs -DNOPAUSE -sDEVICE=jpeg -r%g -sOutputFile=%s.%%06d.jpg temp.ps - < /dev/null'%(res,prefix))
os.chdir('..')

# --- Remove ps file
os.system('rm -f %s/temp.ps'%prefix)

##########################################################################
# --- Crop the jpeg files using MOGRIFY from ImageMagick
##########################################################################
# --- Parameters chosen to yield 640x640 image that contains title and limited
# --- legend information when applied to standard WARP output.
getfiles = 'find . -name "*.jpg" -print'

os.chdir(prefix)
for file in os.popen(getfiles).readlines():
    name = file[:-1]
    print('cropping file '+name)
    a=int(640*float(res)/100)
    #  b=int(640*float(res)/100)
    b=int(600*float(res)/100)
    c=int(105*float(res)/100)
    d=int(124*float(res)/100)
    os.system('mogrify -crop %gx%g+%g+%g '%(a,b,c,d)+name)

os.chdir('..')
```

To use the script above, one can type the following commands in termminal

```py
# Save all frames from frame 1 to end.
python convertcgmtojpg.py data.cgm

# Save start frame (1) through end frame (10) at a step of framestep (2)
python convertcgmtojpg.py data.cgm 1 10 2
```

## 9. Converting jpg into mp4 files
Often times the `Warp` simulations will save hundreds of sequential jpg files from [Step 8](#8-convert-jpg-into-mp4-files). To do so the following steps can be taken to convert all sequential jpg files into a mp4 for easier viewing experience.

1. Install the `ffmpeg` packages under the `warp_env` with

    ```bash
    conda install -c conda-forge ffmpeg
    ```

2. Then assuming the `convertcgmtojpg.py` has created a directory named `movie.000/`, `cd movie.000/` into the directory and create a `convertjpgtomp4.py`. Copy the following code into the python script and save it.

    ```py
    #!/usr/bin/env python
    ##########################################################################
    # Author: Jean-Luc Vay
    # Date: 11/19/2007
    ##########################################################################
    # This script converts sequential frames to a movie using ffmpeg.
    #
    # To use it, type
    #
    # mkmovie image movie.mp4
    #
    ##########################################################################

    import os
    import sys
    import string

    usage = "\n Usage: mkmovie [-format jpg -fmt %06d] image movie.mp4\n"

    # --- set defaults
    argdict = {'format':'jpg',
            'fmt'   :'%06d',
            'rate'  : 12}

    # --- get arguments
    for i,arg in enumerate(sys.argv):
    if arg[0]=='-':
        if arg[1:] in argdict.keys():
        argdict[arg[1:]] = sys.argv[i+1]
        else:
        print('\n Error in argument list: '+arg+' is not a valid argument')
        print(usage)
        raise('')
        
    input  = sys.argv[-2]
    output = sys.argv[-1]
    fmt = argdict['fmt']
    format = argdict['format']
    rate = int(argdict['rate'])

    #line = 'ffmpeg -y -b 5000 -r %g -i '%rate+input+fmt+'.'+format+' -strict -1 -qscale 1.0 '+output
    line = 'ffmpeg -y -r %g -i '%rate+input+fmt+'.'+format+' -strict -1 -qscale 1.0 '+output
    print(line)
    os.system(line)
    print('done\n')
    ```

3. To use this script, one should type 

    ```bash
    python convertjpgtomovie.py -format jpg -fmt %06d -rate 12 movie.000. movie.mp4
    ```

    And it should generate a `movie.mp4` file for viewing,

<!-- ## 9. Save data into `openPMD` standard.
If saving the `Warp` simulation data, whether it's particle data, or field data, becomes necessary, it's recommended to save the data following the `openPMD` standard. The [`openPMD`](https://www.openpmd.org) standard defines the minimal metadate file information across different packages, thus allowing an easier data analysis and communication efforts across different research groups. `Warp` can easily save data in to the [`HDF5`](https://www.hdfgroup.org/solutions/hdf5/) format, which can be easily visualized by the `openPMD-viewer`.
1. Install `openpmd-viewer`. The command below will automatically install the necessary packages such as `openpmd-api`, `hdf5`, `h5py`, etc.

    ```bash
    conda install -c conda-forge openpmd-viewer
    ```

2. Modify the `Warp` simualtion script to include save data options. An example of saving an electrostatic field data is shown in the script below.

    ```py
    from warp.data_dumping.openpmd_diag import ElectrostaticFieldDiagnostic

    diag1 = ElectrostaticFieldDiagnostic( solver=wp.w3d, comm_world=None, period=5, top=wp.top, w3d=wp.w3d)
    wp.installafterstep( diag1.write )
    ```

**Note:** The code above obviously assumeed that the simulation was 3D, and the solver is the usual w3d solver. In other simulation geometries, the solver should be installed before calling it. And the solver in the args should be updated accordingly.

3. Check the above code created a directory called `diags` under the run directory. This is where the data is being stored at. To view the data. create another python script like the following:

    ```py
    import os
    import matplotlib.pyplot as plt
    import numpy as np
    from openpmd_viewer import OpenPMDTimeSeries

    # Read all data
    ts = OpenPMDTimeSeries('./diags/hdf5/')

    # Extract the electrostatic potential Phi z component at Warp simulation step 5. This is across the x-plane.
    Phiz, info_Phiz = ts.get_field( iteration=5, field='phi', slice_across=['x'])
    print(Phiz)
    print(Phiz.shape)
    print(info_Phiz.axes) # This shows the Ez axes, if you choose the slice_across is x, then the data should be saved with y [axes[0]] and z [axes[1]] axes.

    # The line below shows that there may be an issue in getting the upper and lower limit of the extracted [axes[0]]. The returned array has the same value.
    xaxis = getattr( info_Phiz, info_Phiz.axes[0] )
    print(xaxis)

    # Create the correct grid to plot the Phi_z.
    ny, nz = Phiz.shape

    dy = 0.3/ny
    dz = 4.0/nz

    y = -0.15 + np.arange(ny) * dy
    z = -2.0 + np.arange(nz) * dz

    fig, ax = plt.subplots(figsize=(12, 4))

    image = ax.imshow(
        Phiz,
        origin="lower",
        aspect="auto",
        extent=[z.min(), z.max(), y.min(), y.max()],
        cmap="viridis",
    )

    fig.colorbar(image, ax=ax, label=r"$\Phi$")
    ax.set_xlabel("Z (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title(r"Field $\Phi(Y,Z)$")

    plt.tight_layout()
    plt.show()
    ``` -->

## [Return to Table of contents](#table-of-contents)
