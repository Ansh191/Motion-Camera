import subprocess
from glob import glob

files = glob("/home/pi/Desktop/vids/*.h264")

guptasnet = "/mnt/guptasnet/pi_cam"

# print(files)

for file in files:
    new_file = file[:-4] + "mp4"
    print(subprocess.run(["MP4Box", "-add", file, new_file, "-fps", '24']))
    print(subprocess.run(['mv', new_file, guptasnet]))
    print(subprocess.run(["rm", "-f", file]))
