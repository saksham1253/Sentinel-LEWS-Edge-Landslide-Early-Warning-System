class SMSSimulator:
    def __init__(self, district_code="DST"):
        self.district_code = district_code
        self.outbox = []
        
    def generate_message(self, 
                         timestamp_str: str, 
                         sector_id: str, 
                         lat: float, 
                         lon: float, 
                         zones: list, 
                         url_code: str = "HELP112") -> str:
        """
        Generate a strictly <= 160 char SMS.
        """
        # Format: "{DIS}:{TIME} HIGH landslide risk near {SEC} ({lat:.2f},{lon:.2f}). Evacuate: {ZONES}. Info: {URL}"
        
        # Abbreviate time to HH:MM
        try:
            # Parse ISO if full
            ts_short = timestamp_str[11:16] # T12:34:56 -> 12:34
        except:
            ts_short = timestamp_str
            
        zones_str = ",".join(zones)
        
        # Construct base message
        # "DST:12:34 HIGH Risk! {SEC} ({lat},{lon}) Evac:{ZONES} {URL}"
        
        base_msg = f"{self.district_code}:{ts_short} HIGH RISK {sector_id} ({lat:.2f},{lon:.2f}). Evac:{zones_str}. Info:{url_code}"
        
        if len(base_msg) > 160:
            # Truncate zones first
            available = 160 - (len(base_msg) - len(zones_str))
            zones_str = zones_str[:available-3] + ".."
            base_msg = f"{self.district_code}:{ts_short} HIGH RISK {sector_id} ({lat:.2f},{lon:.2f}). Evac:{zones_str}. Info:{url_code}"
            
        self.outbox.append(base_msg)
        return base_msg
    
    def send_mock(self, msg):
        print(f"[SMS SENDING]: {msg}")
        if len(msg) > 160:
            print("ERROR: SMS > 160 chars!")
        else:
            print("SMS Sent successfully.")
