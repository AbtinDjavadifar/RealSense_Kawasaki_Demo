import pyrealsense2 as rs
import cam
import os
import time

def detect_cams():

    cam_array = []
    ctx = rs.context()
    if len(ctx.devices) > 0:

        for d in ctx.devices:
            print ('Found device: ', \
                    d.get_info(rs.camera_info.name), ' ', \
                    d.get_info(rs.camera_info.serial_number))
            cam_array.append(d)
    else:
        print("No Intel Device connected")
    return cam_array

if __name__ == "__main__":

    cam_array = []
    path = os.getcwd() + '/pics'
    cams = detect_cams()
    running = True

    for c in cams:
        cam_array.append(cam.RealSenseCam(c))    #Adding cam object to cam_array

    try:
        while running:
            input('\nPress Enter for capturing picture')
            print('')
            print('Time need for capturing each pic:')

            for c in cam_array:
                start = time.time()
                c.get_pics()
                end = time.time()
                print(end - start)

            for c in cam_array:
                c.post_processing()

            print('')
            for c in cam_array:
                c.save_img(path)

    finally:
        print('')
        for c in cam_array:
                c.stop_stream()
