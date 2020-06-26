import utils
import os
import time

parser = argparse.ArgumentParser(description='RealSense - Kawasaki')
parser.add_argument('-cm','--capture_mode', help='It can be manual or auto', required=True)
args = vars(parser.parse_args())

if __name__ == "__main__":

    KawasakiRobot()

    cam_array = []
    path = os.getcwd() + '/pics'
    cams = detect_cams()
    running = True

    if args['capture_mode'] == 'manual':

        for c in cams:
            cam_array.append(utils.RealSenseCam(c, capture_mode='manual'))    #Adding cam object to cam_array

    elif args['capture_mode'] == 'auto':

        for c in cams:
            if c.get_info(rs.camera_info.serial_number) == "845112071957":
                cam_array.append(cam.RealSenseCam(c, capture_mode='auto', cam_mode='master'))  # Adding cam object to cam_array
            else:
                cam_array.append(cam.RealSenseCam(c, capture_mode='auto', cam_mode='slave'))  # Adding cam object to cam_array
    else:
        print("Capture mode is not determined. It must be 'manual' or 'auto'.")

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