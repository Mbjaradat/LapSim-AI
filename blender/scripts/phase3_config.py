"""Phase 3 placement derives from measured reach; Phase 1 limits stay untouched."""
from config import JAW_LENGTH

CONTACT_OFFSET = JAW_LENGTH * .7
WORKSPACE_MARGIN = .10
WORKSPACE_SAMPLES = 11
WORKSPACE_GRID = .01
TOKEN_RADIUS = .004
TOKEN_OFFSETS = {'TRAINING_BEAD_LEFT':(-.012,-.015,0),
                 'TRAINING_BEAD_RIGHT':(.012,-.015,0)}
GB_OFFSET = (0,.010,-.015)
GB_LENGTH = .060
LIVER_OFFSET = (0,.090,-.040)
LIVER_RADII = (.110,.055,.045)


def shifted(point, offset):
    return tuple(a+b for a,b in zip(point,offset))
