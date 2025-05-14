import os
import pandas as pd
from typing import Dict, List, Tuple, Optional, DefaultDict
from collections import defaultdict
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, LpInteger
import streamlit as st
from dataclasses import dataclass

@dataclass
class OptimizationInput:
    total_demand: int
    max_delivery_time: int
    selected_warehouses: List[str]
    max_vehicles: Dict[Tuple[str, str], int]  # (warehouse, mode) -> max_vehicles

class DataLoader:
    def __init__(self, data_dir: str = "dataset"):
        self.data_dir = data_dir
        self.warehouses = None
        self.plants = None
        self.modes = None
        self.routes = None
        
    def load_data(self):
        """Load and validate all required data files."""
        try:
            # Load warehouse capacities (tab-separated)
            wh_cap_path = os.path.join(self.data_dir, "wh_capacity.csv")
            self.warehouses = pd.read_csv(wh_cap_path, sep='\t')
            
            # Load plant capacities (tab-separated)
            pl_cap_path = os.path.join(self.data_dir, "pl_capacity.csv")
            self.plants = pd.read_csv(pl_cap_path, sep='\t')
            
            # Load transport modes (tab-separated)
            tp_cap_path = os.path.join(self.data_dir, "tp_capacity.csv")
            self.modes = pd.read_csv(tp_cap_path, sep='\t')
            
            # Load routes (tab-separated)
            route_path = os.path.join(self.data_dir, "tp_route.csv")
            self.routes = pd.read_csv(route_path, sep='\t')
            
            # Strip any whitespace from string columns
            for df in [self.warehouses, self.plants, self.modes, self.routes]:
                str_cols = df.select_dtypes(include=['object']).columns
                df[str_cols] = df[str_cols].apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
            
            # Validate data
            self._validate_data()
            return True
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            import traceback
            st.text(traceback.format_exc())
            return False
    
    def _validate_data(self):
        """Validate the loaded data for consistency."""
        # Check for required columns
        required_columns = {
            'warehouses': ['warehouse_name', 'capacity', 'stock_level'],
            'plants': ['plant_name', 'capacity', 'stock_level'],
            'modes': ['mode_name', 'weight_capacity'],
            'routes': ['origin', 'destination', 'mode_name', 'lead_time (days)', 'total_cost']
        }
        
        for df_name, columns in required_columns.items():
            df = getattr(self, df_name)
            missing = set(columns) - set(df.columns)
            if missing:
                raise ValueError(f"Missing columns in {df_name}: {missing}")

class TransportationOptimizer:
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        self.optimization_input = None
        
    def get_user_input(self):
        """Get user input using Streamlit interface."""
        st.title("Distribution Cost Optimization")
        
        # Display basic info
        st.sidebar.header("Current System Status")
        st.sidebar.metric("Total Warehouse Capacity", f"{self.data_loader.warehouses['capacity'].sum():,} tons")
        st.sidebar.metric("Total Plant Stock", f"{self.data_loader.plants['stock_level'].sum():,} tons")
        
        # User inputs
        st.header("Optimization Parameters")
        
        # Total demand
        max_demand = self.data_loader.plants['stock_level'].sum()
        total_demand = st.number_input(
            "Total Demand (tons)", 
            min_value=1, 
            max_value=max_demand,
            value=min(1000, max_demand)
        )
        
        # Max delivery time
        max_lead_time = int(self.data_loader.routes['lead_time (days)'].max())
        max_delivery_time = st.slider(
            "Maximum Allowed Delivery Time (days)",
            min_value=1,
            max_value=max_lead_time,
            value=min(5, max_lead_time)
        )
        
        # Warehouse selection
        st.subheader("Select Warehouses")
        selected_warehouses = []
        for _, wh in self.data_loader.warehouses.iterrows():
            if st.checkbox(
                f"{wh['warehouse_name']} (Capacity: {wh['capacity']} tons, Stock: {wh['stock_level']} tons)",
                value=True,
                key=f"wh_{wh['warehouse_name']}"
            ):
                selected_warehouses.append(wh['warehouse_name'])
        
        if not selected_warehouses:
            st.warning("Please select at least one warehouse")
            return None
            
        # Max vehicles per warehouse-mode
        st.subheader("Vehicle Limits")
        st.info("Set maximum number of vehicles available for each warehouse and transport mode combination")
        
        max_vehicles = {}
        for wh in selected_warehouses:
            with st.expander(f"{wh} Vehicle Limits"):
                wh_routes = self.data_loader.routes[
                    (self.data_loader.routes['destination'] == wh) & 
                    (self.data_loader.routes['lead_time (days)'] <= max_delivery_time)
                ]
                
                if wh_routes.empty:
                    st.warning(f"No valid routes to {wh} within {max_delivery_time} days")
                    continue
                    
                for _, route in wh_routes.iterrows():
                    mode = route['mode_name']
                    max_veh = st.number_input(
                        f"Max {mode} vehicles to {wh}",
                        min_value=1,
                        max_value=100,
                        value=10,
                        key=f"veh_{wh}_{mode}"
                    )
                    max_vehicles[(wh, mode)] = max_veh
        
        if not max_vehicles:
            st.error("No valid routes available with current constraints")
            return None
            
        return OptimizationInput(
            total_demand=total_demand,
            max_delivery_time=max_delivery_time,
            selected_warehouses=selected_warehouses,
            max_vehicles=max_vehicles
        )
    
    def build_cost_model(self, input_data: OptimizationInput):
        """Build and solve the cost optimization model."""
        model = LpProblem("Cost_Minimization", LpMinimize)
        
        # Get valid routes based on selected warehouses and max delivery time
        valid_routes = self._get_valid_routes(input_data)
        
        if not valid_routes:
            st.error("No valid routes found with the current constraints.")
            return None, None
            
        # Create a mapping from (wh, mode) to cost for easier access
        route_costs = {(wh, mode): cost for wh, mode, cost in valid_routes}
        
        # Decision variables - use the same keys as route_costs
        shipments = LpVariable.dicts(
            "Shipment",
            route_costs.keys(),
            lowBound=0,
            cat=LpInteger
        )
        
        # Objective: Minimize total cost
        model += lpSum(
            shipments[wh, mode] * cost
            for (wh, mode), cost in route_costs.items()
        ), "Total_Cost"
        
        # Add constraints
        self._add_constraints(model, shipments, input_data, route_costs)
        
        return model, shipments
    
    def build_time_model(self, input_data: OptimizationInput):
        """Build and solve the time optimization model."""
        model = LpProblem("Time_Minimization", LpMinimize)
        
        # Get valid routes
        valid_routes = self._get_valid_routes(input_data)
        
        if not valid_routes:
            st.error("No valid routes found with the current constraints.")
            return None, None, None
            
        # Create a mapping of (warehouse, mode) to cost and lead time
        route_info = {}
        lead_times = {}
        
        for wh, mode, cost in valid_routes:
            route_info[(wh, mode)] = cost
            # Find the lead time for this route
            route = self.data_loader.routes[
                (self.data_loader.routes['destination'] == wh) & 
                (self.data_loader.routes['mode_name'] == mode)
            ].iloc[0]
            lead_times[(wh, mode)] = route['lead_time (days)']
        
        # Decision variables - use the same keys as route_info
        shipments = LpVariable.dicts(
            "Shipment",
            route_info.keys(),
            lowBound=0,
            cat=LpInteger
        )
        
        # Create binary variables to track if a route is used
        route_used = LpVariable.dicts(
            "Route_Used",
            route_info.keys(),
            cat='Binary'
        )
        
        # Big M for the max time constraint
        M = max(lead_times.values()) + 1
        
        # Add constraints to link route_used with shipments
        for (wh, mode) in route_info.keys():
            # If shipments[wh, mode] > 0 then route_used[wh, mode] = 1
            model += route_used[wh, mode] * 0.0001 <= shipments[wh, mode], f"Route_Used_Lower_{wh}_{mode}"
            model += route_used[wh, mode] * M >= shipments[wh, mode], f"Route_Used_Upper_{wh}_{mode}"
        
        # Objective: Minimize maximum delivery time (using max of all used routes)
        max_time = LpVariable("Max_Delivery_Time", lowBound=0)
        model += max_time, "Minimize_Max_Delivery_Time"
        
        # Add constraints for max time
        for (wh, mode), lead_time in lead_times.items():
            # If this route is used, then max_time >= lead_time
            model += max_time >= lead_time - M * (1 - route_used[wh, mode]), f"Max_Time_{wh}_{mode}"
        
        # Add other constraints
        self._add_constraints(model, shipments, input_data, route_info)
        
        return model, shipments, max_time
    
    def _get_valid_routes(self, input_data: OptimizationInput):
        """Get valid routes based on input constraints."""
        valid_routes = []
        
        for _, route in self.data_loader.routes.iterrows():
            wh = route['destination'].strip()
            mode = route['mode_name'].strip()
            
            # Check if warehouse is selected and within max delivery time
            if (wh in input_data.selected_warehouses and 
                route['lead_time (days)'] <= input_data.max_delivery_time and
                (wh, mode) in input_data.max_vehicles):
                
                valid_routes.append((wh, mode, route['total_cost']))
        
        return valid_routes
    
    def _add_constraints(self, model, shipments, input_data, route_costs):
        """Add constraints to the optimization model."""
        # Warehouse capacity and stock level mapping
        warehouse_info = {
            row['warehouse_name']: {
                'capacity': row['capacity'],
                'stock_level': row['stock_level']
            }
            for _, row in self.data_loader.warehouses.iterrows()
        }
        
        # Vehicle capacity mapping
        vehicle_capacities = dict(zip(
            self.data_loader.modes['mode_name'],
            self.data_loader.modes['weight_capacity']
        ))
        
        # 1. Total demand must be met
        model += lpSum(
            shipments[wh, mode] * vehicle_capacities[mode]
            for (wh, mode) in route_costs.keys()
        ) >= input_data.total_demand, "Total_Demand"
        
        # 2. Warehouse capacity constraints (considering stock level)
        for wh in input_data.selected_warehouses:
            if wh in warehouse_info:
                available_capacity = max(0, warehouse_info[wh]['capacity'] - warehouse_info[wh]['stock_level'])
                model += lpSum(
                    shipments[wh2, mode] * vehicle_capacities[mode]
                    for (wh2, mode) in route_costs.keys()
                    if wh2 == wh
                ) <= available_capacity, f"Capacity_{wh}"
        
        # 3. Vehicle limit constraints
        for (wh, mode), max_veh in input_data.max_vehicles.items():
            if (wh, mode) in shipments:  # Check if this combination exists
                model += shipments[wh, mode] <= max_veh, f"Max_Vehicles_{wh}_{mode}"
    
    def solve(self, input_data: OptimizationInput):
        """Solve both optimization models and return results."""
        results = {}
        
        # Solve cost optimization
        cost_model, cost_vars = self.build_cost_model(input_data)
        if cost_model is None or cost_vars is None:
            st.error("Failed to build cost optimization model. Please check your input parameters.")
            results['cost_optimization'] = {
                'status': 'Infeasible',
                'solution': {},
                'total_cost': None
            }
        else:
            cost_model.solve()
            
            if LpStatus[cost_model.status] == 'Optimal':
                cost_solution = {}
                total_cost = 0
                
                # First, collect all non-zero shipments
                for (wh, mode), var in cost_vars.items():
                    val = int(var.varValue)
                    if val > 0:
                        if wh not in cost_solution:
                            cost_solution[wh] = {}
                        cost_solution[wh][mode] = val
                        
                        # Calculate the cost for this shipment
                        route = self.data_loader.routes[
                            (self.data_loader.routes['destination'] == wh) & 
                            (self.data_loader.routes['mode_name'] == mode)
                        ].iloc[0]
                        total_cost += val * route['total_cost']
                
                results['cost_optimization'] = {
                    'status': 'Optimal',
                    'solution': cost_solution,
                    'total_cost': total_cost
                }
            else:
                results['cost_optimization'] = {
                    'status': LpStatus[cost_model.status],
                    'solution': {},
                    'total_cost': None
                }
        
        # Solve time optimization
        time_model, time_vars, max_time_var = self.build_time_model(input_data)
        if time_model is None or time_vars is None or max_time_var is None:
            st.error("Failed to build time optimization model. Please check your input parameters.")
            results['time_optimization'] = {
                'status': 'Infeasible',
                'solution': {},
                'max_delivery_time': None,
                'total_cost': None
            }
        else:
            time_model.solve()
            
            if LpStatus[time_model.status] == 'Optimal':
                time_solution = {}
                total_cost = 0
                
                # First, collect all non-zero shipments
                for (wh, mode), var in time_vars.items():
                    val = int(var.varValue)
                    if val > 0:
                        if wh not in time_solution:
                            time_solution[wh] = {}
                        time_solution[wh][mode] = val
                        
                        # Calculate the cost for this shipment
                        route = self.data_loader.routes[
                            (self.data_loader.routes['destination'] == wh) & 
                            (self.data_loader.routes['mode_name'] == mode)
                        ].iloc[0]
                        total_cost += val * route['total_cost']
                
                # Calculate the actual maximum lead time for this solution
                max_lead_time = 0
                for (wh, mode), count in time_vars.items():
                    if count.varValue > 0:
                        route = self.data_loader.routes[
                            (self.data_loader.routes['destination'] == wh) & 
                            (self.data_loader.routes['mode_name'] == mode)
                        ].iloc[0]
                        max_lead_time = max(max_lead_time, route['lead_time (days)'])
                
                results['time_optimization'] = {
                    'status': 'Optimal',
                    'solution': time_solution,
                    'max_lead_time': max_lead_time,
                    'total_cost': total_cost
                }
            else:
                results['time_optimization'] = {
                    'status': LpStatus[time_model.status],
                    'solution': {},
                    'max_lead_time': None,
                    'total_cost': None
                }
        return results
    
    def get_user_input(self):
        """Dapatkan parameter input dari pengguna."""
        st.sidebar.header("Parameter Input")
        
        # Input total permintaan
        total_demand = st.sidebar.number_input(
            "Total Permintaan (ton)",
            min_value=1,
            value=1000,
            step=100
        )
        
        # Input waktu pengiriman maksimum
        max_delivery_time = st.sidebar.number_input(
            "Waktu Pengiriman Maksimum (hari)",
            min_value=1,
            value=7,
            step=1
        )
        
        # Pemilihan gudang
        st.sidebar.subheader("Pilih Gudang")
        warehouse_options = self.data_loader.warehouses['warehouse_name'].tolist()
        selected_warehouses = st.sidebar.multiselect(
            "Pilih gudang yang akan digunakan dalam optimasi",
            warehouse_options,
            default=warehouse_options[:3]  # Default 3 gudang pertama
        )
        
        # Batas kendaraan dengan section yang bisa di-collapse
        st.sidebar.subheader("Batas Kendaraan")
        max_vehicles = {}
        
        # Dapatkan moda transportasi yang tersedia
        transport_modes = self.data_loader.modes['mode_name'].tolist()
        
        for wh in selected_warehouses:
            # Buat expander untuk setiap gudang
            with st.sidebar.expander(f"📦 {wh}", expanded=False):
                for mode in transport_modes:
                    max_vehicles[(wh, mode)] = st.number_input(
                        f"Maks {mode}",
                        min_value=0,
                        value=5,
                        step=1,
                        key=f"max_{wh}_{mode}",
                        help=f"Jumlah maksimum kendaraan {mode} untuk {wh}"
                    )
        
        return OptimizationInput(
            total_demand=total_demand,
            max_delivery_time=max_delivery_time,
            selected_warehouses=selected_warehouses,
            max_vehicles=max_vehicles
        )
    
    def _get_route_info(self, wh, mode):
        """Get route information including weight capacity and lead time."""
        try:
            route = self.data_loader.routes[
                (self.data_loader.routes['destination'] == wh) & 
                (self.data_loader.routes['mode_name'] == mode)
            ].iloc[0]
            
            # Get weight capacity for this mode
            mode_info = self.data_loader.modes[
                self.data_loader.modes['mode_name'] == mode
            ].iloc[0]
            
            return {
                'weight_capacity': mode_info['weight_capacity'],
                'lead_time_days': route['lead_time (days)'],
                'cost_per_trip': route['total_cost']
            }
        except (IndexError, KeyError):
            return None

    def _display_results(self, results):
        """Tampilkan hasil optimasi dalam Streamlit."""
        st.header("Hasil Optimasi")
        
        # Hasil Optimasi Biaya
        st.subheader("1. Optimasi Biaya")
        cost_result = results.get('cost_optimization', {})
        
        if not cost_result or cost_result['status'] != 'Optimal':
            st.warning("❌ Tidak ditemukan solusi optimal untuk optimasi biaya.")
            if cost_result and 'status' in cost_result:
                st.write(f"Status: {cost_result['status']}")
        else:
            st.success("✅ Ditemukan solusi optimal untuk optimasi biaya!")
            st.write(f"**Total Biaya:** ${cost_result['total_cost']:,.2f}")
            
            if cost_result.get('solution'):
                # Siapkan informasi pengiriman detail
                shipment_details = []
                total_weight = 0
                
                for wh, modes in cost_result['solution'].items():
                    for mode, count in modes.items():
                        if count > 0:
                            route_info = self._get_route_info(wh, mode)
                            if route_info:
                                weight = count * route_info['weight_capacity']
                                total_weight += weight
                                shipment_details.append({
                                    'Gudang': wh,
                                    'Moda': mode,
                                    'Jumlah Kendaraan': count,
                                    'Berat per Kendaraan (ton)': route_info['weight_capacity'],
                                    'Total Berat (ton)': weight,
                                    'Waktu Tempuh (hari)': route_info['lead_time_days'],
                                    'Biaya per Perjalanan ($)': route_info['cost_per_trip'],
                                    'Total Biaya ($)': count * route_info['cost_per_trip']
                                })
                
                # Tampilkan ringkasan
                st.write(f"**Total Berat Dikirim:** {total_weight:,.1f} ton")
                
                # Tampilkan rencana pengiriman detail
                st.write("**Rencana Pengiriman:**")
                cost_df = pd.DataFrame(shipment_details)
                st.dataframe(cost_df.style.format({
                    'Berat per Kendaraan (ton)': '{:.1f}',
                    'Total Berat (ton)': '{:,.1f}',
                    'Waktu Tempuh (hari)': '{:.1f}',
                    'Biaya per Perjalanan ($)': '${:,.2f}',
                    'Total Biaya ($)': '${:,.2f}'
                }))
                
                # Tampilkan waktu tempuh maksimum
                if not cost_df.empty:
                    max_lead_time = cost_df['Waktu Tempuh (hari)'].max()
                    st.write(f"**Waktu Tempuh Maksimum:** {max_lead_time:.1f} hari")
            else:
                st.warning("Tidak ada rencana pengiriman yang dihasilkan.")
        
        st.divider()
        
        # Hasil Optimasi Waktu
        st.subheader("2. Optimasi Waktu")
        time_result = results.get('time_optimization', {})
        cost_result = results.get('cost_optimization', {})
        
        if not time_result or time_result['status'] != 'Optimal':
            st.warning("❌ Tidak ditemukan solusi optimal untuk optimasi waktu.")
            if time_result and 'status' in time_result:
                st.write(f"Status: {time_result['status']}")
        else:
            # Hitung waktu tempuh maksimum untuk solusi biaya
            cost_max_lead_time = 0
            if cost_result.get('solution'):
                for wh, modes in cost_result['solution'].items():
                    for mode, count in modes.items():
                        if count > 0:
                            route_info = self._get_route_info(wh, mode)
                            if route_info:
                                cost_max_lead_time = max(cost_max_lead_time, route_info['lead_time_days'])
            
            # Hanya tampilkan solusi optimasi waktu jika lebih baik dari optimasi biaya
            if time_result.get('max_lead_time', float('inf')) < cost_max_lead_time:
                st.success("✅ Ditemukan solusi dengan waktu tempuh maksimum yang lebih singkat!")
                st.write(f"**Waktu Tempuh Maksimum:** {time_result['max_lead_time']:.1f} hari (vs {cost_max_lead_time:.1f} hari pada solusi optimasi biaya)")
                st.write(f"**Total Biaya:** ${time_result['total_cost']:,.2f}")
                
                if time_result.get('solution'):
                    # Siapkan informasi pengiriman detail
                    shipment_details = []
                    total_weight = 0
                    
                    for wh, modes in time_result['solution'].items():
                        for mode, count in modes.items():
                            if count > 0:
                                route_info = self._get_route_info(wh, mode)
                                if route_info:
                                    weight = count * route_info['weight_capacity']
                                    total_weight += weight
                                    shipment_details.append({
                                        'Gudang': wh,
                                        'Moda': mode,
                                        'Jumlah Kendaraan': count,
                                        'Berat per Kendaraan (ton)': route_info['weight_capacity'],
                                        'Total Berat (ton)': weight,
                                        'Waktu Tempuh (hari)': route_info['lead_time_days'],
                                        'Biaya per Perjalanan ($)': route_info['cost_per_trip'],
                                        'Total Biaya ($)': count * route_info['cost_per_trip']
                                    })
                    
                    # Tampilkan ringkasan
                    st.write(f"**Total Berat Dikirim:** {total_weight:,.1f} ton")
                    
                    # Tampilkan rencana pengiriman detail
                    st.write("**Rencana Pengiriman:**")
                    time_df = pd.DataFrame(shipment_details)
                    st.dataframe(time_df.style.format({
                        'Berat per Kendaraan (ton)': '{:.1f}',
                        'Total Berat (ton)': '{:,.1f}',
                        'Waktu Tempuh (hari)': '{:.1f}',
                        'Biaya per Perjalanan ($)': '${:,.2f}',
                        'Total Biaya ($)': '${:,.2f}'
                    }))
            else:
                st.info("ℹ️ Solusi optimasi waktu tidak memberikan waktu tempuh maksimum yang lebih baik dibandingkan solusi optimasi biaya.")
                st.write(f"**Waktu Tempuh Maksimum Terbaik yang Dapat Dicapai:** {cost_max_lead_time:.1f} hari")

def main():
    """Fungsi utama untuk menjalankan aplikasi Streamlit."""
    st.set_page_config(
        page_title="Optimasi Transportasi",
        page_icon="🚚",
        layout="wide"
    )
    
    # Create a header with title on left and logo on right
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("🚚 Optimasi Rantai Pasok")
        st.write("Optimalkan biaya dan waktu pengiriman untuk rantai pasok Anda.")
    
    with col2:
        logo_path = os.path.join("assets", "Logo_Pupuk_Indonesia_(Persero)")
        if os.path.exists(logo_path + ".png"):
            logo_path += ".png"
        elif os.path.exists(logo_path + ".jpg"):
            logo_path += ".jpg"
            
        if os.path.exists(logo_path):
            st.image(
                logo_path,
                width=120,  # Slightly smaller for top-right placement
                output_format="PNG"
            )
    
    # Inisialisasi data loader
    data_loader = DataLoader()
    
    try:
        data_loader.load_data()
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()
    
    # Inisialisasi optimizer
    optimizer = TransportationOptimizer(data_loader)
    
    # Dapatkan input pengguna
    with st.sidebar:
        st.header("Parameter Input")
        input_data = optimizer.get_user_input()
    
    # Jalankan optimasi
    if st.button("Jalankan Optimasi"):
        with st.spinner("Menjalankan optimasi..."):
            results = optimizer.solve(input_data)
            optimizer._display_results(results)

if __name__ == "__main__":
    main()
