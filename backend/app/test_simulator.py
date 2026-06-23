import os
import cantools

def test_dbc_loading_and_decoding():
    # 1. Get path to DBC
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dbc_path = os.path.join(current_dir, "..", "bms.dbc")
    
    print(f"Loading DBC from: {dbc_path}")
    assert os.path.exists(dbc_path), f"DBC file does not exist at {dbc_path}"
    
    # 2. Parse DBC
    db = cantools.database.load_file(dbc_path)
    
    # Verify expected message names
    message_names = [msg.name for msg in db.messages]
    print(f"DBC Messages parsed: {message_names}")
    assert "BMS_Status" in message_names
    assert "BMS_PackVals" in message_names
    assert "BMS_Temps" in message_names
    
    # 3. Test Status Message encoding/decoding
    status_msg = db.get_message_by_name("BMS_Status")
    test_data = {
        'BMS_SOC': 78.5,          # 78.5%
        'BMS_State': 2,          # Charging
        'BMS_ErrorFlags': 4,     # OverTemp
        'BMS_Counter': 45,
        'BMS_Checksum': 0
    }
    encoded = status_msg.encode(test_data)
    assert len(encoded) == 8, "BMS_Status raw length should be 8 bytes"
    
    decoded = status_msg.decode(encoded)
    assert abs(decoded['BMS_SOC'] - 78.5) < 0.01
    assert decoded['BMS_State'] == 'Charging'
    assert decoded['BMS_ErrorFlags'] == 4
    assert decoded['BMS_Counter'] == 45
    
    # 4. Test PackVals Message encoding/decoding
    pack_msg = db.get_message_by_name("BMS_PackVals")
    test_vals = {
        'BMS_PackVoltage': 398.2,  # 398.2 V
        'BMS_PackCurrent': -24.5,  # -24.5 A
        'BMS_AvgCellVolt': 4.148,  # 4.148 V
        'BMS_CellVoltDev': 0.015   # 0.015 V
    }
    encoded_vals = pack_msg.encode(test_vals)
    decoded_vals = pack_msg.decode(encoded_vals)
    assert abs(decoded_vals['BMS_PackVoltage'] - 398.2) < 0.01
    assert abs(decoded_vals['BMS_PackCurrent'] - -24.5) < 0.01
    assert abs(decoded_vals['BMS_AvgCellVolt'] - 4.148) < 0.001
    assert abs(decoded_vals['BMS_CellVoltDev'] - 0.015) < 0.001

    # 5. Test Temps Message encoding/decoding
    temps_msg = db.get_message_by_name("BMS_Temps")
    test_temps = {
        'BMS_MaxCellTemp': 41,    # 41 C
        'BMS_MinCellTemp': 38,    # 38 C
        'BMS_AvgCellTemp': 40,    # 40 C
        'BMS_TempSensorCount': 4
    }
    encoded_temps = temps_msg.encode(test_temps)
    decoded_temps = temps_msg.decode(encoded_temps)
    assert decoded_temps['BMS_MaxCellTemp'] == 41
    assert decoded_temps['BMS_MinCellTemp'] == 38
    assert decoded_temps['BMS_AvgCellTemp'] == 40
    
    print("DBC validation unit tests completed successfully!")

if __name__ == "__main__":
    test_dbc_loading_and_decoding()
