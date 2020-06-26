import pyrealsense2 as rs
import numpy as np
import datetime
from skimage import io
import time
import cv2

import subprocess

class KawasakiRobot():
    """
    Runs the demo on Kawasaki robot and triggers the cameras
    """
    def __init__(self):
        process = subprocess.Popen('plink -telnet 192.168.0.2', bufsize=-1, shell=True, stdout=subprocess.PIPE,
                                   stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        log = ''
        out = process.stdout.read(1).decode('utf-8')

        while out != '' and process.poll() == None:
            log += out
            if (': ' in log):
                break
            process.stdout.flush()
            out = process.stdout.read(1).decode('utf-8')
        process.stdout.flush()

        if ("login" in log):
            process.stdin.write('as\n\n'.encode())  # should i include login: ?
            print('robot is connected')

        command = "EXECUTE WRINKLER\n"

        process.stdin.write(command.encode())
        process.stdin.flush()


class RealSenseCam():
    """
    Required functions for capturing images using multiple RealSense cameras
    """
    def __init__(self, cam, capture_mode='manual', cam_mode=None):
        """
        :param cam: camera id
        :param capture_mode: 'manual' or 'auto'
        :param cam_mode: 'master' or 'slave'
        """
        self.cam = cam
        self.color_img = None
        self.depth_img = None
        self.depth_image_3d = None
        self.frames = None

        self.id = self.get_cam_id()

        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_device(self.id)

        # self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        # self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        self.profile = self.pipeline.start(self.config)
        self.depth_sensor = self.profile.get_device().first_depth_sensor()

        if self.depth_sensor.supports(rs.option.inter_cam_sync_mode):
            if capture_mode == 'manual':
                    if self.id == "845112071957":
                        self.depth_sensor.set_option(rs.option.inter_cam_sync_mode, 1) #Master = 1
                        print("{} is set as master".format(self.id))
                    else:
                        self.depth_sensor.set_option(rs.option.inter_cam_sync_mode, 2) #Slave = 2
                        print("{} is set as slave".format(self.id))
            elif capture_mode == 'auto':
                if cam_mode == 'master':
                        self.depth_sensor.set_option(rs.option.inter_cam_sync_mode, 1)  # Master = 1
                        print("{} is set as master".format(self.id))
                elif cam_mode == 'slave':
                        self.depth_sensor.set_option(rs.option.inter_cam_sync_mode, 2)  # Slave = 2
                        print("{} is set as slave".format(self.id))
                else:
                    print("Camera mode is not determined. It must be 'master' or 'slave'.")
            else:
                print("Capture mode is not determined. It must be 'manual' or 'auto'.")

        if self.depth_sensor.supports(rs.option.depth_units):
            self.depth_sensor.set_option(rs.option.depth_units, 0.001)
            print("Depth unit = 0.001")

        if self.depth_sensor.supports(rs.option.emitter_enabled):
            self.depth_sensor.set_option(rs.option.emitter_enabled, 1.0)
            print("Emmiter --> Enabled")

        self.depth_scale = self.depth_sensor.get_depth_scale()

        print("Depth Scale is: " , self.depth_scale)
        clipping_distance_in_meters = 2.5 #1 meter
        self.clipping_distance = clipping_distance_in_meters / self.depth_scale

        align_to = rs.stream.color
        self.align = rs.align(align_to)

    def get_cam_id(self):
        return self.cam.get_info(rs.camera_info.serial_number)

    def get_pics(self):
        self.frames = self.pipeline.wait_for_frames()

    def post_processing(self):
        aligned_frames = self.align.process(self.frames)

        # frames.poll_frames()
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        # if not depth_frame or not color_frame:
        #     continue

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        self.color_img = color_image
        self.depth_img = depth_image

        gray_color = 153
        depth_image_3d = np.dstack((self.depth_img,self.depth_img,self.depth_img)) #depth image is 1 channel, color is 3 channels
        bg_removed = np.where((depth_image_3d > self.clipping_distance) | (depth_image_3d <= 0), gray_color, self.color_img)

        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(self.depth_img, alpha=0.07), cv2.COLORMAP_JET)
        # images = np.hstack((bg_removed, depth_colormap))

        self.depth_img = depth_colormap
        self.depth_image_3d = bg_removed

        # # Show images
        # cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        # cv2.imshow('RealSense', images)
        # cv2.waitKey(1)

    def save_img(self, path, color=True, depth=True):
        now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%02S')

        temp_path = path + '/' + now_time + '_' + self.id

        if self.color_img is not None and color is True:
            self.color_img = np.uint8(self.color_img)
            # io.imsave(temp_path + '_color.jpg', self.color_img)
            cv2.imwrite(temp_path + '_color.jpg',self.color_img)

        if self.depth_img is not None and depth is True:
            self.depth_img = np.uint8(self.depth_img)
            # io.imsave(temp_path + '_depth.jpg', self.depth_img)
            cv2.imwrite(temp_path + '_depth.jpg',self.depth_img)

        if self.depth_img is not None and depth is True:
            self.depth_img = np.uint8(self.depth_image_3d)
            # io.imsave(temp_path + '_depth_3D.jpg', self.depth_image_3d)
            cv2.imwrite(temp_path + '_depth_3D.jpg',self.depth_image_3d)

        print('Saved pictures for cam ' + self.id + ' at ' + temp_path)

    def stop_stream(self):
        self.pipeline.stop()
        print('Pipeline for camera %s stopped!' % self.id)

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