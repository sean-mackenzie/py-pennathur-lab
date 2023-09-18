
# --- SOURCE-MEASURE CAPABILITIES

# NOTE: V-source protection sets the maximum voltage level the SourceMeter can output
k2410_voltage_source_protection = [20, 40, 100, 200, 300, 400, 500, None]  # V (None > 500 V)
# the power-on default is NONE.
# to change, use command:           :SOUR:VOLT:PROT 20

k2410_voltage_ranges = [0.2, 2, 20, 1000]  # V  --> The "range" set the limits for the other functions
k2410_voltage_source_range = [0.21, 2.1, 21, 1100]  # V (correspond to the voltage ranges)
k2410_voltage_measure_range = [0.211, 2.11, 21.1, 1100]  # V (correspond to the voltage ranges)
k2410_voltage_compliance_range = [0.21, 2.1, 21, 1100]  # V (correspond to the voltage ranges)
# NOTE: "compliance" is equivalent to "protection"

k2410_current_range = [1, 10, 100, 1000, 20000]  # micro Amps
k2410_current_source_range = [1.05, 10.5, 105, 1050, 21000]  # micro Amps (correspond to the current ranges)
k2410_current_measure_range = [1.055, 10.55, 105.5, 1055, 21100]  # micro Amps (correspond to the current ranges)
k2410_current_compliance_range = [1.05, 10.5, 105, 1050, 21000]  # micro Amps (correspond to the current ranges)
# NOTE: "compliance" is equivalent to "protection"

k2410_max_power = 22  # Watts


# --- DEFAULT SETTINGS BELOW
auto_zero = 'On'
beeper = 'ON'
digits = 5
filter = 'OFF'
guard = 'CABLE'

ohms_source_mode = 'AUTO'

output_output_enable = 'DISABLED'
output_off_state = 'Normal*'
output_auto_off = 'DISABLED'

auto_range = 'ENABLED'

relative = 'OFF'
relative_value = 0.0

sense_mode = '2-wire'

source_delay = 1  # milliseconds
auto_delay = 'ENABLED'

speed = 1  # Normal (1 PLC)

sweep = 'Linear staircase'
sweep_start = 0  # V or A
sweep_stop = 0  # V or A
sweep_step = 0  # V or A
sweep_count = 1
sweep_pts = 2500
sweep_source_ranging = 'best fixed'
sweep_abort_on_compliance = 'OFF'

voltage_protection = 'NONE'

triggering_arm_layer_event = 'IMMediate'
triggering_arm_layer_count = 1
triggering_arm_layer_output_trigger = 'Line #2, OFF'

triggering_trigger_layer_event = 'IMMediate'
triggering_trigger_layer_count = 1
triggering_trigger_layer_output_trigger = 'Line #2, ALL OFF'
triggering_trigger_layer_delay = 0.0  # seconds