"""STK COM Interface Test Script.

Tests whether STK 11 COM automation works on this machine,
bypassing Connect API limitations.
"""

import sys

def test_com():
    try:
        import win32com.client
        print("[OK] win32com available")
    except ImportError:
        print("[FAIL] win32com not installed. Run: pip install pywin32")
        sys.exit(1)

    # Try connecting to STK
    print("\n--- Connecting to STK via COM ---")
    stk_app = None
    for prog_id in ["STK12.Application", "STK11.Application", "STK.Application"]:
        try:
            stk_app = win32com.client.GetActiveObject(prog_id)
            print(f"[OK] Connected via {prog_id}")
            break
        except Exception:
            pass

    if stk_app is None:
        # Try creating new instance
        for prog_id in ["STK12.Application", "STK11.Application", "STK.Application"]:
            try:
                stk_app = win32com.client.Dispatch(prog_id)
                stk_app.Visible = True
                print(f"[OK] Created new STK instance via {prog_id}")
                break
            except Exception as e:
                print(f"[INFO] {prog_id} Dispatch failed: {e}")

    if stk_app is None:
        print("[FAIL] Cannot connect to STK via COM")
        sys.exit(1)

    # Get root object
    root = stk_app.Personality2
    print(f"[OK] Got IAgStkObjectRoot")

    # Check current scenario
    if root.Children.Count > 0:
        scenario = root.Children(0)
        print(f"[OK] Current scenario: {scenario.InstanceName}")
    else:
        print("[INFO] No scenario loaded, creating one...")
        scenario = root.NewScenario("COMTest")
        print(f"[OK] Created scenario: COMTest")

    # List existing satellites
    sats = scenario.Children.GetElements(18)  # eSatellite = 18
    print(f"[INFO] Existing satellites: {sats.Count}")
    for i in range(sats.Count):
        print(f"  - {sats.Item(i).InstanceName}")

    # Create two test satellites
    print("\n--- Creating test satellites ---")

    # Satellite 1: Primary
    try:
        sat1 = scenario.Children.New(18, "Primary")  # eSatellite = 18
    except Exception:
        sat1 = scenario.Children.Item("Primary")
        print("[INFO] Primary already exists, reusing")

    sat1_iface = sat1
    print(f"[OK] Satellite 'Primary' ready")

    # Set orbit using SetState (COM method)
    try:
        sat1_iface.SetState(
            "Classical HPOP UseScenarioInterval 60 J2000 "
            '"14 Jun 2026 16:00:00.000" 6778137 0.0007 51.64 0 0 0'
        )
        print("[OK] Primary orbit set (Classical HPOP)")
    except Exception as e:
        # Try via Connect command through COM
        try:
            root.ExecuteCommand(
                'SetState */Satellite/Primary Classical HPOP UseScenarioInterval 60 J2000 '
                '"14 Jun 2026 16:00:00.000" 6778137 0.0007 51.64 0 0 0'
            )
            print("[OK] Primary orbit set via ExecuteCommand")
        except Exception as e2:
            print(f"[WARN] Primary SetState failed: {e2}")

    # Satellite 2: Debris
    try:
        sat2 = scenario.Children.New(18, "Debris")  # eSatellite = 18
    except Exception:
        sat2 = scenario.Children.Item("Debris")
        print("[INFO] Debris already exists, reusing")

    sat2_iface = sat2
    print(f"[OK] Satellite 'Debris' ready")

    try:
        sat2_iface.SetState(
            "Classical HPOP UseScenarioInterval 60 J2000 "
            '"14 Jun 2026 16:00:00.000" 6778500 0.001 51.7 5 5 180'
        )
        print("[OK] Debris orbit set (Classical HPOP)")
    except Exception as e:
        try:
            root.ExecuteCommand(
                'SetState */Satellite/Debris Classical HPOP UseScenarioInterval 60 J2000 '
                '"14 Jun 2026 16:00:00.000" 6778500 0.001 51.7 5 5 180'
            )
            print("[OK] Debris orbit set via ExecuteCommand")
        except Exception as e2:
            print(f"[WARN] Debris SetState failed: {e2}")

    # Propagate both
    print("\n--- Propagating ---")
    try:
        sat1_iface.Propagate()
        print("[OK] Primary propagated")
    except Exception:
        root.ExecuteCommand("Propagate */Satellite/Primary")
        print("[OK] Primary propagated via ExecuteCommand")

    try:
        sat2_iface.Propagate()
        print("[OK] Debris propagated")
    except Exception:
        root.ExecuteCommand("Propagate */Satellite/Debris")
        print("[OK] Debris propagated via ExecuteCommand")

    # Test ACAT via COM
    print("\n--- Testing ACAT via COM ---")

    # Create AdvCAT object via Connect (through COM)
    try:
        root.ExecuteCommand("New / */AdvCAT COMTest Ignore")
        print("[OK] AdvCAT object created")
    except Exception as e:
        print(f"[WARN] AdvCAT creation failed: {e}")

    # Configure ACAT
    try:
        root.ExecuteCommand("ACAT */AdvCAT/COMTest Threshold 10")
        print("[OK] Threshold set to 10 km")
    except Exception as e:
        print(f"[WARN] Threshold failed: {e}")

    # Try adding primary/secondary with BOTH path formats
    for path_fmt in ["Satellite/Primary", "*/Satellite/Primary"]:
        try:
            root.ExecuteCommand(f"ACAT */AdvCAT/COMTest Primary Add {path_fmt}")
            print(f"[OK] Primary added with path: {path_fmt}")
            break
        except Exception as e:
            print(f"[INFO] Primary Add failed with '{path_fmt}': {e}")

    for path_fmt in ["Satellite/Debris", "*/Satellite/Debris"]:
        try:
            root.ExecuteCommand(f"ACAT */AdvCAT/COMTest Secondary Add {path_fmt}")
            print(f"[OK] Secondary added with path: {path_fmt}")
            break
        except Exception as e:
            print(f"[INFO] Secondary Add failed with '{path_fmt}': {e}")

    # Compute
    try:
        root.ExecuteCommand("ACAT */AdvCAT/COMTest Compute")
        print("[OK] ACAT computation completed")
    except Exception as e:
        print(f"[WARN] ACAT Compute failed: {e}")

    # Get events
    try:
        result = root.ExecuteCommand("ACATEvents_RM */AdvCAT/COMTest")
        print(f"[OK] ACAT events result: {result}")
    except Exception as e:
        print(f"[WARN] ACATEvents_RM failed: {e}")

    # Test position query
    print("\n--- Testing position query ---")
    try:
        result = root.ExecuteCommand("AER */Satellite/Primary */Satellite/Debris")
        lines = str(result).split("\n")[:3]
        print(f"[OK] AER data (first 3 lines):")
        for line in lines:
            print(f"  {line}")
    except Exception as e:
        print(f"[WARN] AER query failed: {e}")

    print("\n=== COM Interface Test Complete ===")


if __name__ == "__main__":
    test_com()
