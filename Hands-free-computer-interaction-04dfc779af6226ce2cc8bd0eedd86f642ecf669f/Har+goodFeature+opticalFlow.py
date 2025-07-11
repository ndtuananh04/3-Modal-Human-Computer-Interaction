import cv2
import time
import numpy as np
import pyautogui
import copy
import math
dwell_start_time = 0
dwell_threshold = 1.0  # giây
mouse_prev_pos = pyautogui.position()
dwell_radius = 15  # bán kính vùng đứng yên
tmp = False
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
face_location = None
new_face_loc = None
corner = np.zeros((1,1))
vx = 0
vy = 0
old_vx = 0
old_vy = 0
done = False
target_time = 1/30
prev_img = None
cur_img = None
cap = cv2.VideoCapture(0)
SMALL_AREA_RATIO = 0.4
new_gray = None
lp_weight = 0.8
while face_location is None:

    ret, cur_img = cap.read()
    if not ret:
        break
    new_gray = cv2.cvtColor(cur_img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(new_gray, scaleFactor=1.1, minNeighbors=3,flags=cv2.CASCADE_FIND_BIGGEST_OBJECT | cv2.CASCADE_DO_CANNY_PRUNING,minSize=(65, 65))

    # Put detected faces into the queue
    if len(faces) > 0:
        face_location = faces[0]

while True:

    start = time.time()
    frame = copy.deepcopy(cur_img)
    prev_img = copy.deepcopy(cur_img)

    ret, cur_img = cap.read()
    gray = new_gray
    if(new_face_loc is not None):
        face_location = new_face_loc



    # x,y,w,h là các tham số của track area con
    x =int (face_location[0] + face_location[2] * ((1.0 - SMALL_AREA_RATIO) / 2.0))  # quỷ vcl sao nó cứ track 1 bên mắt
    y =int (face_location[1] + face_location[3] * ((1.0 - SMALL_AREA_RATIO) / 2.0)) 
    w =int (face_location[2] * SMALL_AREA_RATIO)
    h =int (face_location[3] * SMALL_AREA_RATIO)
    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 255), 2)
    track_area = gray[y:y+h, x:x+w]
    cv2.rectangle(frame, (face_location[0], face_location[1]), (face_location[0] + face_location[2], face_location[1] + face_location[3]), (255, 0, 0), 2)

    
    corner = cv2.goodFeaturesToTrack(track_area, maxCorners=20, qualityLevel=0.001, minDistance=2)
    termcrit = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 20, 0.03)
    if corner.size > 0:
        cv2.cornerSubPix(track_area, corner, winSize=(5, 5), zeroZone=(-1, -1), criteria=termcrit)
    corner += np.array([x, y], dtype=np.float32)
    corner -= np.array([face_location[0], face_location[1]], dtype=np.float32)



    new_gray = cv2.cvtColor(cur_img, cv2.COLOR_BGR2GRAY)
    new_corners, status, err = cv2.calcOpticalFlowPyrLK(
        gray[face_location[1]:face_location[1]+face_location[3],face_location[0]:face_location[0]+face_location[2]], 
        new_gray[face_location[1]:face_location[1]+face_location[3],face_location[0]:face_location[0]+face_location[2]], corner, None, 
        winSize=(11, 11), 
        maxLevel=0, 
        criteria=(cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 14, 0.03)
    )



    valid_indices = (status == 1) & (corner[:, :, 0] >= 0) & (corner[:, :, 0] < face_location[2]) & (corner[:, :, 1] >= 0) & (corner[:, :, 1] < face_location[3])
    valid_m_corners = corner[valid_indices]
    valid_new_corners = new_corners[valid_indices]


    for corner_m, corner_new in zip(valid_m_corners, valid_new_corners):
        x1, y1 = int(corner_m[0] + face_location[0]), int(corner_m[1] + face_location[1])
        x2, y2 = int(corner_new[0] + face_location[0]), int(corner_new[1] + face_location[1])

        # Vẽ đường thẳng nối 2 điểm bằng màu xanh lá cây (BGR: (0, 255, 0))
        cv2.line(frame, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)



    dx = valid_new_corners[:, 0] - valid_m_corners[:, 0]  # Hiệu tọa độ x
    if(len(dx)):
        mean_dx = np.sum(dx) / len(dx)
    else:
        mean_dx = 0
    dy = valid_new_corners[:, 1] - valid_m_corners[:, 1]  # Hiệu tọa độ y
    if(len(dy)):
        mean_dy = np.sum(dy) / len(dy)
    else:
        mean_dy = 0

    faces = face_cascade.detectMultiScale(new_gray, scaleFactor=1.5, minNeighbors=2,flags=cv2.CASCADE_FIND_BIGGEST_OBJECT | cv2.CASCADE_DO_CANNY_PRUNING,minSize=(65, 65))
    if len(faces) > 0:
        new_face_loc = faces[0]
        tx = new_face_loc[0] + new_face_loc[2]/2 - face_location[0] - face_location[2]/2
        ty = new_face_loc[1] + new_face_loc[3]/2 - face_location[1] - face_location[3]/2
        face_location = new_face_loc
    else:
        tx = 0
        ty = 0
        face_location[0]+=mean_dx
        face_location[1]+=mean_dy
        new_face_loc = None
    vx = -mean_dx * 20 + 5 * tx
    vy = mean_dy * 20 - 5 * ty

    # code hiệu chỉnh vx, vy

    # low pass filter
    vx = vx * (1-lp_weight) + old_vx * lp_weight
    vy = vy * (1-lp_weight) + old_vy * lp_weight
    old_vx = vx
    old_vy = vy

    # tính gia tốc

    distance = math.sqrt(vx*vx+vy*vy)

    if (distance < 20):
        vx = vx/3
        vy = vy/3
    pyautogui.PAUSE = 0
    pyautogui.moveRel(vx, vy, duration=0)
    if distance <= dwell_radius:
        if time.time() - dwell_start_time > dwell_threshold and tmp is True:
            pyautogui.click()
            tmp = False
    else:
        dwell_start_time = time.time()
        tmp = True    
    cv2.imshow('Face Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    if target_time-time.time()+start > 0 :
        time.sleep(target_time-time.time()+start)



#face_location dựa hết vào prev_img.
#Bây h, cần 1 pipeline mới, để lấy face_location mới mà di chuột
#Nếu có facelocation mới thì update vị trí mới?
#Không thì + mean_dx, mean_dy


# mean_dx, mean_dy nhiều vấn đề vcl (bằng 1 cách nào đó nó nhiễu vđ?)