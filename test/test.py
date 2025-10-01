import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer


async def init_dut(dut):
    """Initialize DUT with clock, reset, and basic setup"""
    clock = Clock(dut.clk, 1, units="ms")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    dut.ui_in.value = 0b00000001
    dut.uio_in.value = 0

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    
    dut.rst_n.value = 0
    await Timer(100, units="ps")
    dut.rst_n.value = 1
    await Timer(100, units="ps")
    
    # Check that counter is reset to 0 immediately (async reset)
    reset_value = int(dut.uio_out.value)
    assert reset_value == 0, f"Async reset assertion failed: expected 0, got {reset_value}"


@cocotb.test()
async def test_counting(dut):
    dut._log.info("Testing counter")
    
    await init_dut(dut)
    await ClockCycles(dut.clk, 1)

    # === Test Normal Counting ===
    dut._log.info("Testing normal counting")
    for expected_count in range(1, 10):
        await ClockCycles(dut.clk, 1)
        actual = int(dut.uio_out.value)
        dut._log.info(f"Clock cycle, expected: {expected_count}, actual: {actual}")
        assert actual == expected_count, f"Expected {expected_count}, got {actual}"

    dut._log.info("Testing reset during counting")

    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 1)
    reset_value = int(dut.uio_out.value)
    assert reset_value == 0, f"Mid-execution reset failed: expected 0, got {reset_value}"

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    assert int(dut.uio_out.value) == 1, f"Post-reset counting failed: expected 1, got {int(dut.uio_out.value)}"

    # === Test Overflow Behavior ===
    dut._log.info("Testing overflow behavior")
    
    await ClockCycles(dut.clk, 253)
    
    assert int(dut.uio_out.value) == 254
    
    # Count to 255
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 255, f"Expected 255, got {int(dut.uio_out.value)}"
    
    # Test overflow: 255 -> 0
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 0, f"Overflow failed: expected 0, got {int(dut.uio_out.value)}"
    
    # Continue counting after overflow
    await ClockCycles(dut.clk, 1)
    assert int(dut.uio_out.value) == 1, f"Post-overflow counting failed: expected 1, got {int(dut.uio_out.value)}"


@cocotb.test()
async def test_counter_load_values(dut):
    dut._log.info("Testing load")

    await init_dut(dut)

    # Test loading different values
    test_values = [42, 100, 255, 0, 128]
    
    for test_val in test_values:
        dut._log.info(f"Testing load of value {test_val}")
        
        dut.uio_in.value = test_val
        
        dut.ui_in.value = 0b00000000  # Assert load_n=0
        await ClockCycles(dut.clk, 2)
        
        actual = int(dut.uio_out.value)
        assert actual == test_val, f"Load failed: expected {test_val}, got {actual}"
        
        dut.ui_in.value = 0b00000001
        await ClockCycles(dut.clk, 1)
        expected_next = (test_val + 1) & 0xFF
        actual_next = int(dut.uio_out.value)
        assert actual_next == expected_next, f"Count after load failed: expected {expected_next}, got {actual_next}"


@cocotb.test()
async def test_counter_output_enable(dut):
    dut._log.info("Testing output enable control")

    await init_dut(dut)

    dut.ui_in.value = 0b00000011
    await ClockCycles(dut.clk, 1)
    
    # Check that uio_oe = 0 (outputs disabled)
    uio_oe_value = int(dut.uio_oe.value)
    dut._log.info(f"uio_oe value when output_enable_n=1: {uio_oe_value}")
    # The output enable should be 0 when output_enable_n is asserted
    assert uio_oe_value == 0, f"Expected uio_oe=0 when output disabled, got {uio_oe_value}"

    dut.ui_in.value = 0b00000001
    await ClockCycles(dut.clk, 1)
    
    # Check that uio_oe is now enabled (non-zero)
    uio_oe_value = int(dut.uio_oe.value)
    dut._log.info(f"uio_oe value when output_enable_n=0: {uio_oe_value}")
    # The output enable should be non-zero when output_enable_n is deasserted
    assert uio_oe_value != 0, f"Expected uio_oe!=0 when output enabled, got {uio_oe_value}"
