import time
import pylablib as pll
pll.par["devices/dlls/andor_sdk2"] = "path/to/dlls"
from pylablib.devices import Andor
# cam = Andor.AndorSDK3Camera()

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

test_example4 = True
if test_example4:
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

    import matplotlib.pyplot as plt
    plt.imshow(images[-1])
    plt.show()