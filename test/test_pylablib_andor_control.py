import time

import pylablib as pll
from numpy import number

pll.par["devices/dlls/andor_sdk2"] = "path/to/dlls"
from pylablib.devices import Andor

# ---

test_example1 = True
if test_example1:
    print("Number of Andor cameras: {}".format(Andor.get_cameras_number_SDK2()))

test_example2 = False
if test_example2:
    cam = Andor.AndorSDK2Camera(idx=0)
    cam.close()

test_example3 = False
if test_example3:
    cam = Andor.AndorSDK2Camera(temperature=-80, fan_mode="full")
    print("All Amp modes: {}".format(cam.get_all_amp_modes()))
    print("Max vsspeed: {}".format(cam.get_max_vsspeed()))
    print(cam.get_full_info())
    # AndorSDK2Camera.set_amp_mode()
    # AndorSDK2Camera.set_vsspeed()
    cam.close()

# Test acquiring images and plot
test_example4 = False
if test_example4:
    import matplotlib.pyplot as plt  # for plotting

    with Andor.AndorSDK2Camera() as cam:  # connect to the devices
        # change some camera parameters
        cam.set_exposure(50E-3)
        cam.set_roi(0, 128, 0, 128, hbin=2, vbin=2)
        cam.setup_shutter("open")
        # start camera acquisition
        wavelength = 770E-9  # initial wavelength (in meters)
        images = []
        cam.start_acquisition()
        while wavelength < 720E-9:
            print("set laser wavelength: {}".format(wavelength))  # tune the laser frequency (using coarse tuning)
            time.sleep(0.5)  # wait until the laser stabilizes
            cam.wait_for_frame()  # ensure that there's a frame in the camera queue
            img = cam.read_newest_image()
            images.append(img)
            wavelength += 0.5E-9

    plt.imshow(images[-1])
    plt.show()

# Test acquiring images and save
test_example5 = False
if test_example5:
    import numpy as np  # import numpy for saving
    from tifffile import imwrite

    # connect to the devices
    with Andor.AndorSDK2Camera() as cam:
        # change some camera parameters
        cam.set_exposure(50E-3)
        cam.set_roi(0, 128, 0, 128, hbin=2, vbin=2)
        # start the stepping loop
        images = []
        for _ in range(10):
            time.sleep(0.5)  # wait
            img = cam.snap()  # grab a single frame
            images.append(img)

    np.array(images).astype("<u2").tofile("frames.bin")  # save frames as raw binary
    imwrite('temp.tif', np.array(images, dtype='uint16'), photometric='minisblack')

# Test acquire images continuously but starting acquisition is delayed by setting up acquisition
test_example6 = False
if test_example6:
    with Andor.AndorSDK2Camera() as cam:  # to close the camera automatically
        cam.start_acquisition()  # start acquisition (automatically sets it up as well)
        i = 0
        while i < 10:  # acquisition loop
            cam.wait_for_frame()  # wait for the next available frame
            frame = cam.read_oldest_image()  # get the oldest image which hasn't been read yet
            # ... process frame ...
            i += 1

# Test continuous acquisition, where setup occurs ahead of starting acquisition (so starting is precise)
test_example7 = False
if test_example7:
    cam = Andor.AndorSDK2Camera()  # connect to the camera
    nframes = 20  # nframes=100 relates to the size of the frame buffer; the acquisition will continue indefinitely
    time_to_stop = 10  # could be same or different as nframes

    # setup (slow)
    cam.setup_acquisition(mode="sequence", nframes=nframes)  # could be combined with start_acquisition, or kept separate
    i = 0

    cam.start_acquisition()
    while True:  # acquisition loop
        cam.wait_for_frame(since="lastread", nframes=1, timeout=20., error_on_stopped=False)  # wait for the next available frame
        frame = cam.read_oldest_image(peek=False, return_info=False)  # get the oldest image which hasn't been read yet
        # ... process frame ...
        i += 1
        if i > time_to_stop:
            break
    cam.stop_acquisition()

    cam.close()

# Test continuous acquisition, where multiple images are acquired at a time
test_example8 = False
if test_example8:
    cam = Andor.AndorSDK2Camera()  # connect to the camera
    nframes_buffer = 8  # size of the frame buffer; can set to the number of images to acquire per step?
    nframes_acquire = 5  # probably want buffer to be slightly larger to allow overflow?
    number_of_steps = 5  # could be number of voltage levels

    # setup (slow)
    cam.setup_acquisition(mode="sequence", nframes=nframes_buffer)

    cam.start_acquisition()
    for i in range(number_of_steps):  # acquisition loop
        cam.wait_for_frame(since="now", nframes=nframes_acquire, timeout=20., error_on_stopped=False)
        # since="now": wait until nframes are acquired since this call was made (proxy for voltage was set?)

        rng = cam.get_new_images_range()
        frames, info = cam.read_multiple_images(rng=(rng[1]-nframes_acquire,rng[1]),  # read the newest n images
                                                peek=False, missing_frame="skip",
                                                return_info=True,  # NOTE: returning info may take long, so not good for speed
                                                return_rng=False)

        # ... process frame ...
        i += 1
        if i > time_to_stop:
            break
    cam.stop_acquisition()

    cam.close()