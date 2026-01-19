from abc import ABC, abstractmethod
import random

class DataProvider(ABC):
    @abstractmethod
    def get_wip_by_layout_bins(self, bin_codes):
        pass

    @abstractmethod
    def get_counts_by_layout_bins(self, bin_codes):
        """
        Fetch summary counts (e.g. number of cassettes) for a list of bins.
        Returns: { bin_code: count }
        """
        pass

class MockDataProvider(DataProvider):
    def get_wip_by_layout_bins(self, bin_codes):
        """
        Generates random Mock Data simulating:
        select sheet_id_chip_id,grade,model_no,stage_id,cassette_id from celods.r_chip_wip_ods
        select cassette_id,position from beolpptsn.r_cst_cst
        """
        results = {}
        
        for code in bin_codes:
            # Random chance to be empty
            if random.random() > 0.9:
                results[code] = []
                continue
                
            # Generate 1-5 Cassettes per Bin
            cassettes = []
            num_cst = random.randint(1, 5)
            
            for i in range(num_cst):
                cst_id = f"CST-{random.randint(1000, 9999)}"
                
                # Generate wips inside cassette
                wips = []
                num_wips = random.randint(10, 30)
                for j in range(num_wips):
                    wips.append({
                        'sheet_id_chip_id': f"S{random.randint(10,99)}-CH{random.randint(100,999)}",
                        'grade': random.choice(['A', 'A', 'A', 'B', 'P', 'B', 'A']),
                        'model_no': random.choice(['TX-2024', 'RX-9900', 'AI-CHIP-V1', 'TX-PRO', 'NM-100']),
                        'stage_id': random.choice(['LITH', 'ETCH', 'DEP', 'CMP', 'CLEAN', 'PHOTO']),
                        'op_id': f"OP-{random.randint(200, 500)}"
                    })
                    
                cassettes.append({
                    'cassette_id': cst_id,
                    'position': i + 1,
                    'wips': wips
                })
            
            results[code] = cassettes
            
        return results

    def get_counts_by_layout_bins(self, bin_codes):
        results = {}
        for code in bin_codes:
            # Consistent with get_wip_by_layout_bins mock logic
            if random.random() > 0.9:
                results[code] = 0
            else:
                results[code] = random.randint(1, 5)
        return results
    def __init__(self, celods_uri, beol_uri):
        self.celods_uri = celods_uri
        self.beol_uri = beol_uri
        
    def get_wip_by_layout_bins(self, bin_codes):
        """
        Implementation strategy for Oracle:
        1. Query beolpptsn.r_cst_cst using bin_codes (mapping bin codes to location if needed)
           Query: select cassette_id, position from beolpptsn.r_cst_cst where location in :bin_codes
        2. Query celods.r_chip_wip_ods using found cassette_ids
           Query: select sheet_id_chip_id, grade, model_no, stage_id, cassette_id from celods.r_chip_wip_ods 
                  where cassette_id in :cassette_ids
        """
        # Note: This is a placeholder for real cx_Oracle / oracledb logic.
        # User can switch to this provider via config.
        print(f"DEBUG: OracleDataProvider called for bins {bin_codes}")
        
        # Real SQL queries provided by user:
        # SQL_WIP = "select sheet_id_chip_id, grade, model_no, stage_id, cassette_id from celods.r_chip_wip_ods"
        # SQL_CST = "select cassette_id, position from beolpptsn.r_cst_cst"
        
    def get_counts_by_layout_bins(self, bin_codes):
        # Placeholder for Oracle counts query
        # select location, count(cassette_id) from beolpptsn.r_cst_cst where location in :bin_codes group by location
        print(f"DEBUG: OracleDataProvider.get_counts called for {len(bin_codes)} bins")
        return {code: 0 for code in bin_codes}

def get_data_provider(config):
    if config['USE_MOCK_DATA']:
        return MockDataProvider()
    else:
        return OracleDataProvider(config.get('ORACLE_CELODS_URI'), config.get('ORACLE_BEOL_URI'))
