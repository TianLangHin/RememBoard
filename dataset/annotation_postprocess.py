# Every game can be annotated on CVAT using object tracking,
# dragging only when a position changes and thus creating a keyframe.
# However, this causes interpolation in non-keyframes,
# which in CVAT can only be done by manually setting everything to a keyframe.
# The other option is to propagate a bounding box every time a move is made,
# but this causes many unnecessary duplicates and resets changes.

# Thus, the fastest way to manually annotate all such games is by allowing
# the interpolation on non-keyframes to happen, download the annotations in CVAT 1.1 video format,
# and then manually adjust each of the non-keyframes to take the value of the last seen keyframe
# as well as setting it to be a keyframe, and then loading it back into CVAT.

import sys
import xml.etree.ElementTree as ET

file_in, file_out = sys.argv[1], sys.argv[2]

COPY_ATTRS = ['occluded', 'xtl', 'ytl', 'xbr', 'ybr', 'z_order']

tree = ET.parse(file_in)
root = tree.getroot()

# The root <annotations> tag contains a number of <track> child nodes.
for track in root.iter('track'):
    # To overwrite automatic interpolations, we keep track of our last keyframe.
    last_keyframe = None
    # Within each <track>, there is a series of <box> nodes representing each frame.
    for box in track.iter('box'):
        # The very first box is always a keyframe.
        if last_keyframe is None:
            last_keyframe = box
            continue
        attributes = box.attrib
        # We now need to edit the attributes to match the last keyframe if the current
        # frame is not a keyframe.
        if attributes['keyframe'] == '0':
            # Ensures no additional interpolation occurs (and makes rerunning this script a no-op).
            box.set('keyframe', '1')
            # We set everything to what was in our last keyframe.
            for attr in COPY_ATTRS:
                box.set(attr, last_keyframe.attrib[attr])
        elif attributes['keyframe'] == '1':
            # Here, we see a new keyframe.
            last_keyframe = box
        # We assume the very last box within a track is marked "outside" and a "keyframe".

tree.write(sys.argv[2], short_empty_elements=False)
