# Elbow fit check against a skeleton model (indicative only)

Loads the right humerus/ulna/radius meshes and elbow joint definition from the OpenSim `Arm26` model
(https://github.com/opensim-org/opensim-models, `Geometry/arm_r_*.vtp` and `Models/Arm26/arm26.osim`; clone it to `/tmp/osm`),
puts the elbow centre on the exo's elbow axis, and sweeps a soft-tissue envelope through the exo STLs.

- This is a generic adult skeleton, NOT Adhrit's arm. Replace the numbers with measured ones before trusting any result.
- Soft tissue is a rough envelope (tubes from the arm circumferences, plus 8 mm over the distal humerus).
- Result so far: the straight forearm cuffs assume the forearm lies along the upper-arm axis, but the model's forearm sits about 12 deg lateral (carrying angle).
