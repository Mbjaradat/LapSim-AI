"""Phase 3B presentation only. Validated control/mechanics settings are untouched."""
SOURCE_SCALE = .0008  # source units assumed mm; 0.8 presentation scale, not metric validation
SOURCE_NECK = (48.387262, 22.876199, -6.055609)
SOURCE_FUNDUS = (88.077115, 94.137934, -26.327782)
SOURCE_BODY = (79.007337, 55.726724, -15.571631)
NECK_OFFSET = (0, .018, -.018)  # relative to Phase 3A measured neutral-contact midpoint
LIVER_VOXEL = .0015
LIVER_SMOOTH_ITERATIONS = 5
LIVER_DECIMATE = .55
GB_DECIMATE = .45
CAMERA_LOCATION = (0, -.185, -.155)
CAMERA_AIM = (0, .050, -.066)
CAMERA_LENS = 29.0
CAVITY_CENTER = (0, .025, -.075)
CAVITY_RADII = (.245, .255, .185)
CAVITY_RINGS = 32
CAVITY_SEGMENTS = 96
ASSET_FOLDER = 'assets/third_party/anatomy/spl_liver_2014'
