"""Trainer layout in metres; all poses checked against existing joint limits."""
SEAT_HEIGHT = -.110
BOARD_TOP = SEAT_HEIGHT-.002
BOARD_CENTER = (0,.042,BOARD_TOP-.0055)  # Separate base from inset to avoid coplanar faces.
BOARD_DIMENSIONS = (.106,.086,.008)
RING_RADIUS = .0055
RING_THICKNESS = .0016
PEG_RADIUS = .0018
PEG_HEIGHT = .008
HANDOFF = (0,.042,-.080)
SOURCES = {f'RING_{i+1}':(x,y,SEAT_HEIGHT)
           for i,(x,y) in enumerate((x,y) for y in (.020,.042,.064) for x in (-.033,-.014))}
TARGETS = {name:(-p[0],p[1],p[2]) for name,p in SOURCES.items()}
CAMERA_POSITION = (0,-.105,.025)
CAMERA_TARGET = (0,.042,-.099)
CAMERA_LENS = 48
