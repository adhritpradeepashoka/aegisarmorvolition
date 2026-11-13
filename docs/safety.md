# Safety notes

- Hardware e-stop (22 mm pushbutton) must cut servo power, independent of software.
- Physical end stops on elbow (and wrist) so a servo or software fault cannot push the joint past its safe range. Current design target: extension stop near 0 deg, flexion stop near 90 deg (the real elbow can go further; the limit is a deliberate choice).
- Software torque limit and current limit. DS51150 stall current is 7.4-8.3 A (vendor page): use a fused supply sized for it.
- Elbow reaction torque stays inside the arm (internal force pair across the elbow). The chest link carries the exo's weight and keeps it from slipping; it does not take the elbow torque.
- Test without a person first (hang a weight, run the full range, check stops engage).
- Everything printed is untested placeholder geometry until you have test-fitted and load-tested it yourself.
