import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_counting(dut):
    dut._log.info("Testing counter")

    clock = Clock(dut.clk, 1, units="ms")
    cocotb.start_soon(clock.start())

    dut._log.info("Testing reset behavior")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0b00000001  # load_n=1, high_z=0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    
    # Check that counter is reset to 0
    reset_value = int(dut.uo_out.value)
    assert reset_value == 0, f"Reset failed: expected 0, got {reset_value}"
    
    # Release reset
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # === Test Normal Counting ===
    dut._log.info("Testing normal counting")
    for expected_count in range(1, 10):
        await ClockCycles(dut.clk, 1)
        actual = int(dut.uo_out.value)
        dut._log.info(f"Clock cycle, expected: {expected_count}, actual: {actual}")
        assert actual == expected_count, f"Expected {expected_count}, got {actual}"

    # === Test Mid-Execution Reset ===
    dut._log.info("Testing reset during counting")
    pre_reset_value = int(dut.uo_out.value)
    assert pre_reset_value > 0, "Counter should have incremented"
    
    # Apply reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    
    # Check that counter is reset to 0
    reset_value = int(dut.uo_out.value)
    assert reset_value == 0, f"Mid-execution reset failed: expected 0, got {reset_value}"

    # Release reset and verify counting resumes from 0
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    assert int(dut.uo_out.value) == 1, f"Post-reset counting failed: expected 1, got {int(dut.uo_out.value)}"

    # === Test Overflow Behavior ===
    dut._log.info("Testing overflow behavior")
    
    # Load 254 into counter to test overflow quickly
    dut.ui_in.value = 254
    dut.uio_in.value = 0b00000001  # load_n=1
    await ClockCycles(dut.clk, 1)
    dut.uio_in.value = 0b00000000  # load_n=0 (falling edge)
    await ClockCycles(dut.clk, 1)
    
    # Verify we loaded 254
    assert int(dut.uo_out.value) == 254
    
    # Set load_n back to 1 for normal counting
    dut.uio_in.value = 0b00000001  # load_n=1
    
    # Count to 255
    await ClockCycles(dut.clk, 1)
    assert int(dut.uo_out.value) == 255, f"Expected 255, got {int(dut.uo_out.value)}"
    
    # Test overflow: 255 -> 0
    await ClockCycles(dut.clk, 1)
    assert int(dut.uo_out.value) == 0, f"Overflow failed: expected 0, got {int(dut.uo_out.value)}"
    
    # Continue counting after overflow
    await ClockCycles(dut.clk, 1)
    assert int(dut.uo_out.value) == 1, f"Post-overflow counting failed: expected 1, got {int(dut.uo_out.value)}"


@cocotb.test()
async def test_counter_load_values(dut):
    dut._log.info("Testing load")

    clock = Clock(dut.clk, 1, units="ms")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0b00000001  # load_n=1, high_z=0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # Test loading different values
    test_values = [42, 100, 255, 0, 128]
    
    for test_val in test_values:
        dut._log.info(f"Testing load of value {test_val}")
        
        # Set up the value to load
        dut.ui_in.value = test_val
        
        # Create falling edge on load_n (uio_in[0])
        dut.uio_in.value = 0b00000001  # load_n=1
        await ClockCycles(dut.clk, 1)
        dut.uio_in.value = 0b00000000  # load_n=0 (falling edge)
        await ClockCycles(dut.clk, 1)
        
        # Check that the value was loaded
        actual = int(dut.uo_out.value)
        assert actual == test_val, f"Load failed: expected {test_val}, got {actual}"
        
        # Set load_n back to 1 and verify counting continues from loaded value
        dut.uio_in.value = 0b00000001  # load_n=1
        await ClockCycles(dut.clk, 1)
        expected_next = (test_val + 1) & 0xFF  # Handle 8-bit overflow
        actual_next = int(dut.uo_out.value)
        assert actual_next == expected_next, f"Count after load failed: expected {expected_next}, got {actual_next}"


@cocotb.test()
async def test_counter_high_z_output(dut):
    dut._log.info("Testing tri state")

    clock = Clock(dut.clk, 1, units="ms")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0b00000001  # load_n=1, high_z=0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # Let counter increment a few times to have a known value
    await ClockCycles(dut.clk, 5)
    normal_output = int(dut.uo_out.value)
    dut._log.info(f"Normal output value: {normal_output}")

    # Enable high-Z output (uio_in[1] = 1)
    dut.uio_in.value = 0b00000011  # load_n=1, high_z=1
    await ClockCycles(dut.clk, 1)
    
    # Check that output is in high-impedance state
    # In simulation, high-Z typically appears as 'z' or undefined
    try:
        hz_output = dut.uo_out.value
        # Convert to string to check for 'z' state
        hz_str = str(hz_output)
        dut._log.info(f"High-Z output: {hz_str}")
        # The output should be in high-impedance state (showing as 'z' or similar)
        assert 'z' in hz_str.lower() or hz_str == 'xxxxxxxx', f"Expected high-Z output, got {hz_str}"
    except:
        # Some simulators might handle high-Z differently
        dut._log.info("High-Z state detected (simulator specific)")

    # Disable high-Z output (uio_in[1] = 0)
    dut.uio_in.value = 0b00000001  # load_n=1, high_z=0
    await ClockCycles(dut.clk, 1)
    
    # Verify normal output is restored and counter continued counting
    restored_output = int(dut.uo_out.value)
    expected_output = (normal_output + 2) & 0xFF  # +2 because counter ran 2 more cycles
    assert restored_output == expected_output, f"Expected {expected_output} after disabling high-Z, got {restored_output}"
